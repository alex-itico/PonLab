# plot_delay.py
# Uso:
#   python plot_delay.py --outdir out --base mi_topologia_2.pon --algos ipact limited gated
#   # o solo uno:
#   python plot_delay.py --outdir out --base mi_topologia_2.pon --algos ipact
#
# Genera:
#   out/delay_cdf_<cls>.png               (CDF por clase con curvas de cada algoritmo)
#   out/delay_p95_<cls>.png               (p95 por ciclo por clase/algoritmo)
#   out/delay_mean_<cls>.png              (media por ciclo por clase/algoritmo)
#   out/delay_tables_<algo>.csv           (resumen por algoritmo: media/p95 global por clase)
#
# Requiere que existan, por algoritmo:
#   out/<base>_<algo>_packets.csv
#   out/<base>_<algo>_delay_agg.csv

import os, argparse, csv, math
from collections import defaultdict
import matplotlib.pyplot as plt

def read_csv(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        for r in rdr: rows.append(r)
    return rows

def ensure_outdir(d):
    os.makedirs(d, exist_ok=True)

def ns_to_ms(x):
    return float(x) / 1e6

def build_paths(outdir, base, algo):
    return (os.path.join(outdir, f"{base}_{algo}_packets.csv"),
            os.path.join(outdir, f"{base}_{algo}_delay_agg.csv"))

def cdf_data(values):
    if not values: return [], []
    vals = sorted(values)
    n = len(vals)
    xs = vals
    ys = [(i+1)/n for i in range(n)]
    return xs, ys

def plot_cdf_per_class(all_packet_data, outdir):
    # all_packet_data: dict[cls][algo] -> list of delays (ms)
    classes = sorted(all_packet_data.keys())
    for cls in classes:
        plt.figure()
        for algo, arr in sorted(all_packet_data[cls].items()):
            xs, ys = cdf_data(arr)
            if not xs: continue
            plt.plot(xs, ys, label=algo)
        plt.title(f"CDF Delay en cola (ms) – clase {cls}")
        plt.xlabel("Delay (ms)")
        plt.ylabel("F(x)")
        plt.grid(True, linestyle=":", linewidth=0.5)
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(outdir, f"delay_cdf_{cls}.png"), dpi=120)
        plt.close()

def plot_series_per_class(series_map, metric_name, outdir):
    # series_map: dict[cls][algo] -> list[(cycle, value)]
    classes = sorted(series_map.keys())
    for cls in classes:
        plt.figure()
        for algo, pairs in sorted(series_map[cls].items()):
            pairs = sorted(pairs, key=lambda t: t[0])
            xs = [c for c,_ in pairs]
            ys = [v for _,v in pairs]
            plt.plot(xs, ys, marker="o", markersize=3, label=algo)
        plt.title(f"{metric_name} por ciclo – clase {cls}")
        plt.xlabel("Ciclo")
        plt.ylabel(metric_name)
        plt.grid(True, linestyle=":", linewidth=0.5)
        plt.legend()
        plt.tight_layout()
        fname = f"delay_{'p95' if '95' in metric_name else 'mean'}_{cls}.png"
        plt.savefig(os.path.join(outdir, fname), dpi=120)
        plt.close()

def summarize_global(all_packet_data, outdir):
    # Escribe una tabla por algoritmo con media y p95 globales por clase
    # (usando todos los paquetes de todos los ciclos).
    per_algo_cls = defaultdict(lambda: defaultdict(list))
    for cls, per_algo in all_packet_data.items():
        for algo, arr in per_algo.items():
            per_algo_cls[algo][cls].extend(arr)

    for algo, clsmap in per_algo_cls.items():
        rows = []
        for cls, arr in clsmap.items():
            if not arr:
                rows.append({"algorithm": algo, "cls": cls, "n_packets": 0,
                             "mean_ms": 0.0, "p95_ms": 0.0})
                continue
            s = sorted(arr)
            n = len(s)
            mean = sum(s)/n
            p95 = s[int(0.95*(n-1))]
            rows.append({"algorithm": algo, "cls": cls, "n_packets": n,
                         "mean_ms": f"{mean:.6f}", "p95_ms": f"{p95:.6f}"})
        # guardar CSV resumen
        out_csv = os.path.join(outdir, f"delay_tables_{algo}.csv")
        with open(out_csv, "w", newline="", encoding="utf-8") as f:
            hdr = ["algorithm","cls","n_packets","mean_ms","p95_ms"]
            w = csv.DictWriter(f, fieldnames=hdr); w.writeheader()
            for r in rows: w.writerow(r)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", required=True, help="Carpeta donde están los CSV exportados")
    ap.add_argument("--base",   required=True, help="Prefijo base de los archivos (ej: mi_topologia_2.pon)")
    ap.add_argument("--algos",  nargs="+", required=True, help="Algoritmos a graficar (ej: ipact limited gated)")
    args = ap.parse_args()

    ensure_outdir(args.outdir)

    # 1) Leer todos los CSV necesarios
    packets_by_class = defaultdict(lambda: defaultdict(list))    # cls -> algo -> [delay_ms...]
    p95_series_by_class = defaultdict(lambda: defaultdict(list)) # cls -> algo -> [(cycle, p95_ms), ...]
    mean_series_by_class = defaultdict(lambda: defaultdict(list))# cls -> algo -> [(cycle, mean_ms), ...]

    for algo in args.algos:
        p_packets, p_agg = build_paths(args.outdir, args.base, algo)
        if not os.path.exists(p_packets) or not os.path.exists(p_agg):
            print(f"[WARN] Faltan CSV para {algo}: {p_packets} / {p_agg}")
            continue

        # a) packets.csv → delays por paquete
        rows_p = read_csv(p_packets)
        for r in rows_p:
            cls = r["cls"]
            d_ms = ns_to_ms(r["queue_delay_ns"])
            packets_by_class[cls][algo].append(d_ms)

        # b) delay_agg.csv → p95/mean por ciclo
        rows_a = read_csv(p_agg)
        for r in rows_a:
            # solo consideramos entradas con n_packets>0
            n = int(r["n_packets"])
            if n <= 0: continue
            cls = r["cls"]; cyc = int(r["cycle"])
            p95_ms  = ns_to_ms(r["p95_delay_ns"])
            mean_ms = ns_to_ms(r["mean_delay_ns"])
            p95_series_by_class[cls][algo].append((cyc, p95_ms))
            mean_series_by_class[cls][algo].append((cyc, mean_ms))

    # 2) Graficar CDF por clase (curvas por algoritmo)
    plot_cdf_per_class(packets_by_class, args.outdir)

    # 3) Graficar series por clase (p95/mean por ciclo)
    plot_series_per_class(p95_series_by_class, "p95 delay (ms)", args.outdir)
    plot_series_per_class(mean_series_by_class, "mean delay (ms)", args.outdir)

    # 4) Tablas resumen por algoritmo (media y p95 global por clase)
    summarize_global(packets_by_class, args.outdir)

    print("Gráficos y tablas creados en", args.outdir)

if __name__ == "__main__":
    main()
