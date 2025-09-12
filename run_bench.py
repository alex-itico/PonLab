# run_bench.py (reemplazo)
# Ejemplos:
#   python run_bench.py mi_topologia_2.pon ipact limited gated --cycles 200 --outdir out \
#      --algo-params '{"ipact":{"MAX_GRANT_BYTES":12000},"limited":{"MAX_GRANT_BYTES":6000},"gated":{}}'
import sys, os, json, argparse, tempfile, shutil
from core.sim.simulator import Simulator

def write_tmp_pon(base_path, algo, per_algo_params):
    with open(base_path, "r", encoding="utf-8") as f:
        pon = json.load(f)
    sim = pon.setdefault("simulation", {})
    sim["algorithm"] = algo
    # aplica params específicos si existen; si no, deja los globales
    if per_algo_params is not None and algo in per_algo_params:
        sim["algo_params"] = per_algo_params[algo]
    tmp = tempfile.NamedTemporaryFile("w", delete=False, suffix=".pon")
    json.dump(pon, tmp, indent=2)
    tmp.close()
    # copia sidecar si existe
    sidecar_src = base_path + ".profiles.json"
    sidecar_dst = tmp.name + ".profiles.json"
    if os.path.exists(sidecar_src):
        try:
            shutil.copyfile(sidecar_src, sidecar_dst)
        except Exception as e:
            print(f"[warn] No pude copiar sidecar: {e}")
    return tmp.name

def main():
    p = argparse.ArgumentParser()
    p.add_argument("pon", help="Ruta al archivo .pon base")
    p.add_argument("algorithms", nargs="+", help="Algoritmos: ipact, limited, gated, ...")
    p.add_argument("--cycles", type=int, default=None, help="Override ciclos")
    p.add_argument("--outdir", default="out", help="Directorio de salida")
    p.add_argument("--algo-params", default=None,
                   help="JSON con params por algoritmo, ej: '{\"ipact\":{\"MAX_GRANT_BYTES\":12000},\"limited\":{\"MAX_GRANT_BYTES\":6000},\"gated\":{}}'")
    args = p.parse_args()

    per_algo_params = json.loads(args.algo_params) if args.algo_params else None

    os.makedirs(args.outdir, exist_ok=True)
    results = []
    for algo in args.algorithms:
        tmp_pon = write_tmp_pon(args.pon, algo, per_algo_params)
        sim = Simulator(tmp_pon)
        sim.run(cycles=args.cycles, verbose=False)
        out_prefix = os.path.join(args.outdir, f"{os.path.basename(args.pon)}_{algo}")
        paths = sim.export(out_prefix, also_json=True)
        results.append({"algo": algo, **paths})
        # limpieza
        try:
            os.unlink(tmp_pon)
            sc = tmp_pon + ".profiles.json"
            if os.path.exists(sc): os.unlink(sc)
        except Exception:
            pass

    index_path = os.path.join(args.outdir, "index.json")
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print("Exports en:", args.outdir)
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
