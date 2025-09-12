# core/sim/simulator.py
# Simulador con T-CONT (EF/AF/BE), tráfico aleatorio por clase, métricas (throughput/fairness/utilización)
# y ahora Delay/Jitter por paquete con export a CSV/JSON.

from typing import Dict, Any, List, Tuple
import math, random, json, os, csv
from dataclasses import dataclass, asdict

from core.io.pon_loader import load_pon, extract_devices_connections, get_phy_params
from core.phy.rtt_assign import build_onu_rtts
from core.dba.messages import Report, CycleTiming, bytes_to_ns
from core.dba.engine import build_engine

# Algoritmos
import core.dba.alg_ipact      # @register("ipact")
try:
    import core.dba.alg_limited   # @register("limited")
    import core.dba.alg_gated     # @register("gated")
except Exception:
    pass

# ===================== Filas de export =====================

@dataclass
class GrantRow:
    cycle: int
    algorithm: str
    onu_id: str
    grant_bytes: int
    start_ns: int
    end_ns: int

@dataclass
class OnuRow:
    cycle: int
    algorithm: str
    onu_id: str
    offered_bytes: int
    served_bytes: int
    backlog_bytes: int

@dataclass
class CycleRow:
    cycle: int
    algorithm: str
    utilization: float  # 0..1
    fairness_jain: float

@dataclass
class PacketRow:
    cycle: int
    algorithm: str
    onu_id: str
    cls: str
    size_bytes: int
    arrival_ns: int      # arribo a la cola del ONU (tiempo del OLT)
    start_ns: int        # inicio de transmisión del paquete (en OLT timeline)
    end_ns: int          # fin de transmisión
    queue_delay_ns: int  # start_ns - arrival_ns

@dataclass
class DelayAggRow:
    cycle: int
    algorithm: str
    onu_id: str
    cls: str
    n_packets: int
    mean_delay_ns: float
    std_delay_ns: float
    p95_delay_ns: float

# ===================== Stats Recorder =====================

class StatsRecorder:
    def __init__(self, algorithm: str, line_rate_bps: int):
        self.algorithm = algorithm
        self.line_rate_bps = line_rate_bps
        self.cycle_idx = -1

        self._grants: List[GrantRow] = []
        self._per_onu_rows: List[OnuRow] = []
        self._per_cycle_rows: List[CycleRow] = []
        self._packet_rows: List[PacketRow] = []
        self._delay_agg_rows: List[DelayAggRow] = []

        self._per_onu_tmp: Dict[str, Dict[str, int]] = {}
        self._tx_ns_sum = 0
        self._dur_ns_sum = 0

        # para agregados de delay por ONU/clase en el ciclo
        self._delay_map: Dict[Tuple[str,str], List[int]] = {}

    def begin_cycle(self, cycle_idx: int, onu_ids: List[str], classes: List[str]):
        self.cycle_idx = cycle_idx
        self._per_onu_tmp = {onu: {"offered": 0, "served": 0, "backlog": 0} for onu in onu_ids}
        self._tx_ns_sum = 0
        self._dur_ns_sum = 0
        self._delay_map = {(onu,cls): [] for onu in onu_ids for cls in classes}

    def record_offered(self, onu_id: str, inc_bytes: int):
        self._per_onu_tmp[onu_id]["offered"] += int(inc_bytes)

    def record_grant(self, onu_id: str, size_bytes: int, start_ns: int, dur_ns: int):
        end_ns = start_ns + dur_ns
        self._grants.append(GrantRow(self.cycle_idx, self.algorithm, onu_id, int(size_bytes), int(start_ns), int(end_ns)))
        self._per_onu_tmp[onu_id]["served"] += int(size_bytes)
        self._tx_ns_sum += bytes_to_ns(int(size_bytes), self.line_rate_bps)
        self._dur_ns_sum += int(dur_ns)

    def record_packet(self, onu_id: str, cls: str, size_bytes: int, arrival_ns: int, start_ns: int, end_ns: int):
        qdelay = int(start_ns - arrival_ns)
        self._packet_rows.append(PacketRow(
            self.cycle_idx, self.algorithm, onu_id, cls, int(size_bytes),
            int(arrival_ns), int(start_ns), int(end_ns), qdelay
        ))
        self._delay_map[(onu_id, cls)].append(qdelay)

    def set_backlog(self, onu_id: str, backlog_bytes: int):
        self._per_onu_tmp[onu_id]["backlog"] = int(backlog_bytes)

    def end_cycle(self):
        # Per-ONU
        for onu_id, vals in self._per_onu_tmp.items():
            self._per_onu_rows.append(OnuRow(
                self.cycle_idx, self.algorithm, onu_id,
                vals["offered"], vals["served"], vals["backlog"]
            ))
        # Utilización y fairness
        utilization = (self._tx_ns_sum / self._dur_ns_sum) if self._dur_ns_sum > 0 else 0.0
        x = [row.served_bytes for row in self._per_onu_rows if row.cycle == self.cycle_idx]
        if x and sum(x) > 0:
            num = (sum(x) ** 2)
            den = (len(x) * sum(v*v for v in x))
            fairness = float(num / den) if den > 0 else 0.0
        else:
            fairness = 1.0
        self._per_cycle_rows.append(CycleRow(self.cycle_idx, self.algorithm, utilization, fairness))

        # Agregados de delay por ONU/clase en este ciclo
        import statistics as stats
        for (onu,cls), arr in self._delay_map.items():
            if not arr:
                self._delay_agg_rows.append(DelayAggRow(self.cycle_idx, self.algorithm, onu, cls, 0, 0.0, 0.0, 0.0))
                continue
            arr_sorted = sorted(arr)
            n = len(arr_sorted)
            mean = float(sum(arr_sorted)/n)
            std = float(stats.pstdev(arr_sorted)) if n > 1 else 0.0
            p95 = float(arr_sorted[int(0.95*(n-1))])
            self._delay_agg_rows.append(DelayAggRow(self.cycle_idx, self.algorithm, onu, cls, n, mean, std, p95))

    # ---------- Exports ----------
    def export_csv(self, out_prefix: str):
        # grants
        with open(f"{out_prefix}_grants.csv", "w", newline="", encoding="utf-8") as f:
            hdr = ["cycle","algorithm","onu_id","grant_bytes","start_ns","end_ns"]
            w = csv.DictWriter(f, fieldnames=hdr); w.writeheader()
            for row in self._grants: w.writerow(asdict(row))
        # per_onu
        with open(f"{out_prefix}_per_onu.csv", "w", newline="", encoding="utf-8") as f:
            hdr = ["cycle","algorithm","onu_id","offered_bytes","served_bytes","backlog_bytes"]
            w = csv.DictWriter(f, fieldnames=hdr); w.writeheader()
            for row in self._per_onu_rows: w.writerow(asdict(row))
        # per_cycle
        with open(f"{out_prefix}_cycles.csv", "w", newline="", encoding="utf-8") as f:
            hdr = ["cycle","algorithm","utilization","fairness_jain"]
            w = csv.DictWriter(f, fieldnames=hdr); w.writeheader()
            for row in self._per_cycle_rows: w.writerow(asdict(row))
        # packets
        with open(f"{out_prefix}_packets.csv", "w", newline="", encoding="utf-8") as f:
            hdr = ["cycle","algorithm","onu_id","cls","size_bytes","arrival_ns","start_ns","end_ns","queue_delay_ns"]
            w = csv.DictWriter(f, fieldnames=hdr); w.writeheader()
            for row in self._packet_rows: w.writerow(asdict(row))
        # delay aggregates
        with open(f"{out_prefix}_delay_agg.csv", "w", newline="", encoding="utf-8") as f:
            hdr = ["cycle","algorithm","onu_id","cls","n_packets","mean_delay_ns","std_delay_ns","p95_delay_ns"]
            w = csv.DictWriter(f, fieldnames=hdr); w.writeheader()
            for row in self._delay_agg_rows: w.writerow(asdict(row))

    def export_json(self, out_path: str):
        data = {
            "grants": [asdict(r) for r in self._grants],
            "per_onu": [asdict(r) for r in self._per_onu_rows],
            "per_cycle": [asdict(r) for r in self._per_cycle_rows],
            "packets": [asdict(r) for r in self._packet_rows],
            "delay_agg": [asdict(r) for r in self._delay_agg_rows],
        }
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

# ===================== Simulator =====================

class Simulator:
    def __init__(self, pon_path: str):
        self.pon_path = pon_path
        self.pon = load_pon(pon_path)
        self.devices, self.connections = extract_devices_connections(self.pon)
        self.phy = get_phy_params(self.pon)

        # Timing
        self.timing = CycleTiming(
            guard_time_ns= int(self.pon.get("phy",{}).get("guard_time_ns", 1000)),
            line_rate_bps= int(self.pon.get("phy",{}).get("line_rate_bps", 10_000_000_000)),
            scale_m_per_px= self.phy.scale_m_per_px,
            n_fiber= self.phy.n_fiber,
        )

        # Sim config
        simcfg = self.pon.get("simulation", {}) or {}
        self.algo_name   = simcfg.get("algorithm", "ipact")
        self.algo_params = simcfg.get("algo_params", {"MAX_GRANT_BYTES": 12000})
        self.cycles      = int(simcfg.get("cycles", 1))
        self.service_classes = ["EF","AF","BE"]
        self.rng = random.Random(int(simcfg.get("seed", 1234)))

        # Traffic profiles (compat + sidecar)
        traffic = simcfg.get("traffic_profiles", {}) or {}
        self.default_profile = {}
        legacy_be = None
        if "default_onu" in traffic and isinstance(traffic["default_onu"], dict):
            if "BE_bytes_per_cycle" in traffic["default_onu"]:
                legacy_be = int(traffic["default_onu"]["BE_bytes_per_cycle"])

        sidecar_path = f"{pon_path}.profiles.json"
        sidecar_profiles = {}
        if os.path.exists(sidecar_path):
            try:
                with open(sidecar_path, "r", encoding="utf-8") as f:
                    sidecar_profiles = json.load(f) or {}
            except Exception:
                sidecar_profiles = {}

        self.traffic_profiles: Dict[str, Any] = sidecar_profiles if sidecar_profiles else (traffic or {})
        if not self.traffic_profiles and legacy_be is not None:
            self.traffic_profiles = {
                "default_onu": {"BE": {"type":"det","bytes_per_cycle": legacy_be}}
            }
        self.default_profile = self.traffic_profiles.get("default_onu", {}) or {}

        # Packet sizes por clase (por defecto si no vienen en profiles)
        self.default_pkt_size = {"EF": 200, "AF": 1500, "BE": 1500}

        # Engine
        self.engine = build_engine(self.algo_name, self.timing, self.algo_params)

        # RTT(ns)
        self.onu_rtts_ns: Dict[str, int] = build_onu_rtts(self.devices, self.connections, self.phy)

        # Queues por ONU/clase (bytes totales para REPORT)
        self.queues: Dict[str, Dict[str,int]] = {}
        # Colas por paquetes (FIFO)
        self.pkt_queues: Dict[str, Dict[str, List[Dict[str,int]]]] = {}
        # Bytes pendientes que no alcanzan un paquete completo
        self.pending_bytes: Dict[str, Dict[str,int]] = {}

        self.onu_ids: List[str] = []
        for did, d in self.devices.items():
            devtype = (d.get("device_type") or d.get("type"))
            if devtype == "ONU":
                self.onu_ids.append(did)
                self.queues[did] = {c: 0 for c in self.service_classes}
                self.pkt_queues[did] = {c: [] for c in self.service_classes}
                self.pending_bytes[did] = {c: 0 for c in self.service_classes}

        self.now_ns = 0
        self.stats = StatsRecorder(self.algo_name, self.timing.line_rate_bps)
        self._cycle_counter = 0

    # ---------- Helpers de perfiles ----------
    def _sample_poisson(self, lam: float) -> int:
        if lam <= 0: return 0
        if lam > 200.0:
            val = int(round(self.rng.normalvariate(lam, math.sqrt(lam))))
            return max(val, 0)
        L = math.exp(-lam); k = 0; p = 1.0
        while p > L:
            k += 1; p *= self.rng.random()
        return k - 1

    def _gen_bytes_for_profile(self, prof: Dict[str, Any]) -> int:
        if not prof: return 0
        t = str(prof.get("type", "det")).lower()
        if t == "det":
            return int(prof.get("bytes_per_cycle", 0))
        if t == "poisson":
            lam = float(prof.get("lambda_bpc", 0.0))
            return self._sample_poisson(lam)
        if t == "onoff":
            p_on = float(prof.get("p_on", 0.0))
            on_b = int(prof.get("on_bytes_bpc", 0))
            return on_b if self.rng.random() < p_on else 0
        return int(prof.get("bytes_per_cycle", 0))

    def _pkt_size_for(self, onu_id: str, cls: str) -> int:
        # Permite override en profiles: {"EF": {"pkt_size_bytes": 300}, ...}
        prof = self._profile_for(onu_id, cls)
        return int(prof.get("pkt_size_bytes", self.default_pkt_size.get(cls, 1500)))

    def _profile_for(self, onu_id: str, cls: str) -> Dict[str, Any]:
        p_onu = (self.traffic_profiles.get(onu_id, {}) or {})
        if cls in p_onu: return p_onu[cls] or {}
        if cls != "BE" and "BE" in p_onu: return p_onu["BE"] or {}
        if cls in self.default_profile: return self.default_profile[cls] or {}
        if cls != "BE" and "BE" in self.default_profile: return self.default_profile["BE"] or {}
        return {}

    # ---------- Enqueue: genera paquetes y bytes ----------
    def enqueue_demand(self) -> Dict[str, Dict[str, int]]:
        """Devuelve increments (bytes) por ONU/clase para stats."""
        inc_map: Dict[str, Dict[str,int]] = {}
        for onu_id in self.onu_ids:
            inc_map[onu_id] = {}
            for cls in self.service_classes:
                prof = self._profile_for(onu_id, cls)
                inc_bytes = self._gen_bytes_for_profile(prof)

                # Acumula en pending, forma paquetes completos
                pkt_size = self._pkt_size_for(onu_id, cls)
                total = self.pending_bytes[onu_id][cls] + inc_bytes
                n_pkts = total // pkt_size
                self.pending_bytes[onu_id][cls] = total % pkt_size

                # Crear paquetes con arrival = now_ns
                for _ in range(n_pkts):
                    self.pkt_queues[onu_id][cls].append({"size": pkt_size, "arrival_ns": self.now_ns})

                # Bytes visibles para REPORT = paquetes + pending
                bytes_visible = n_pkts * pkt_size + self.pending_bytes[onu_id][cls]
                self.queues[onu_id][cls] += bytes_visible

                inc_map[onu_id][cls] = inc_bytes
        return inc_map

    def make_reports(self) -> List[Report]:
        reports: List[Report] = []
        for onu_id, qdict in self.queues.items():
            rtt = int(self.onu_rtts_ns.get(onu_id, 0))
            ts  = self.now_ns + (rtt // 2)  # llegada al OLT
            reports.append(Report(onu_id=onu_id, queues_bytes=dict(qdict), timestamp_ns=ts))
        return reports

    # ---------- Apply grants: drena por paquetes y registra delay ----------
    def apply_grants(self, grants):
        if not grants: return

        line_bps = self.timing.line_rate_bps
        for g in grants:
            remain = g.size_bytes
            # “cursor” dentro del slot de esta ONU
            cursor_ns = g.start_time_ns

            for cls in self.service_classes:
                if remain <= 0: break

                qpkts = self.pkt_queues[g.onu_id][cls]
                # Sirve paquetes completos en FIFO hasta agotar grant
                new_q = []
                for pkt in qpkts:
                    if remain < pkt["size"]:
                        # no fragmentamos; este y los siguientes quedan para después
                        new_q.append(pkt)
                        continue
                    # servir paquete
                    start_ns = cursor_ns
                    tx_ns = bytes_to_ns(pkt["size"], line_bps)
                    end_ns = start_ns + tx_ns
                    self.stats.record_packet(g.onu_id, cls, pkt["size"], pkt["arrival_ns"], start_ns, end_ns)

                    # actualizar visibilidad en bytes para REPORT
                    self.queues[g.onu_id][cls] -= pkt["size"]
                    remain -= pkt["size"]
                    cursor_ns = end_ns
                # cola remanente (los que no se sirvieron)
                self.pkt_queues[g.onu_id][cls] = new_q

            # Si quedó “remain” pero no hay paquetes suficientes, no lo usamos (guard + ineficiencia).
            # Registrar grant (para throughput/utilización)
            dur_ns = (cursor_ns - g.start_time_ns) + self.timing.guard_time_ns
            # NOTA: respetamos el start del grant del DBA, ajustando dur_ns a lo realmente usado + guard.
            self.stats.record_grant(g.onu_id, g.size_bytes - remain, g.start_time_ns, dur_ns)

        # Avanza el reloj al último fin de slot (considera guard)
        end_times = [row.end_ns for row in []]  # placeholder (no usado)
        # Usamos el end del último grant tal como lo registramos:
        # como no guardamos global, tomamos el máx de lo escrito en _grants del ciclo actual
        if self.stats._grants:
            last_cycle = self.stats.cycle_idx
            ends = [gr.end_ns for gr in self.stats._grants if gr.cycle == last_cycle]
            if ends:
                self.now_ns = max(self.now_ns, max(ends))

    def run_one_cycle(self) -> Tuple[List[Report], List]:
        self.stats.begin_cycle(self._cycle_counter, self.onu_ids, self.service_classes)

        inc_map = self.enqueue_demand()
        for onu_id, clsmap in inc_map.items():
            self.stats.record_offered(onu_id, sum(clsmap.values()))

        reports = self.make_reports()
        grants = self.engine.compute_grants(reports, self.now_ns)
        self.apply_grants(grants)

        # backlog tras servir = bytes visibles (paquetes + pending)
        for onu_id, qdict in self.queues.items():
            self.stats.set_backlog(onu_id, sum(qdict.values()))

        self.stats.end_cycle()
        self._cycle_counter += 1
        return reports, grants

    def run(self, cycles: int = None, verbose: bool = False):
        n = cycles if cycles is not None else self.cycles
        hist = []
        for _ in range(n):
            rep, gr = self.run_one_cycle()
            hist.append((rep, gr))
            if verbose:
                print(f"t={self.now_ns} ns | queues={self.queues}")
        return hist

    # ---------- Exports ----------
    def export(self, out_prefix: str, also_json: bool = True):
        os.makedirs(os.path.dirname(out_prefix), exist_ok=True)
        self.stats.export_csv(out_prefix)
        if also_json:
            self.stats.export_json(out_prefix + ".json")
        return {
            "grants_csv": out_prefix + "_grants.csv",
            "per_onu_csv": out_prefix + "_per_onu.csv",
            "cycles_csv": out_prefix + "_cycles.csv",
            "packets_csv": out_prefix + "_packets.csv",
            "delay_agg_csv": out_prefix + "_delay_agg.csv",
            "json": out_prefix + ".json" if also_json else None
        }