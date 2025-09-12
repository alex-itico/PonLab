# plot_results.py
# Ejemplo:
#   python plot_results.py --per_onu out/mi_topologia_2.pon_ipact_per_onu.csv \
#                          --cycles out/mi_topologia_2.pon_ipact_cycles.csv \
#                          --outdir out
import os, argparse, csv
import matplotlib.pyplot as plt

def read_csv(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        for r in rdr:
            rows.append(r)
    return rows

def plot_throughput_per_onu(per_onu_csv, out_png=None):
    rows = read_csv(per_onu_csv)
    agg = {}
    for r in rows:
        algo = r["algorithm"]
        onu  = r["onu_id"]
        served = int(r["served_bytes"])
        agg.setdefault(algo, {}).setdefault(onu, 0)
        agg[algo][onu] += served
    labels, values = [], []
    for algo in sorted(agg.keys()):
        for onu in sorted(agg[algo].keys()):
            labels.append(f"{algo}:{onu}")
            values.append(agg[algo][onu])
    plt.figure()
    plt.bar(labels, values)
    plt.title("Total Served Bytes por ONU (por algoritmo)")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    if out_png:
        plt.savefig(out_png, dpi=120)
    else:
        plt.show()

def plot_fairness_cycles(cycles_csv, out_png=None):
    rows = read_csv(cycles_csv)
    algos = sorted(set(r["algorithm"] for r in rows))
    cycles = sorted(set(int(r["cycle"]) for r in rows))
    plt.figure()
    for algo in algos:
        xs, ys = [], []
        for c in cycles:
            for r in rows:
                if int(r["cycle"]) == c and r["algorithm"] == algo:
                    xs.append(c); ys.append(float(r["fairness_jain"])); break
        plt.plot(xs, ys, marker="o", label=algo)
    plt.title("Jain's Fairness por ciclo")
    plt.xlabel("Ciclo"); plt.ylabel("Fairness (0..1)")
    plt.legend(); plt.tight_layout()
    if out_png:
        plt.savefig(out_png, dpi=120)
    else:
        plt.show()

def plot_utilization_cycles(cycles_csv, out_png=None):
    rows = read_csv(cycles_csv)
    algos = sorted(set(r["algorithm"] for r in rows))
    cycles = sorted(set(int(r["cycle"]) for r in rows))
    plt.figure()
    for algo in algos:
        xs, ys = [], []
        for c in cycles:
            for r in rows:
                if int(r["cycle"]) == c and r["algorithm"] == algo:
                    xs.append(c); ys.append(float(r["utilization"])); break
        plt.plot(xs, ys, marker="o", label=algo)
    plt.title("Utilización del upstream por ciclo")
    plt.xlabel("Ciclo"); plt.ylabel("Utilización (0..1)")
    plt.legend(); plt.tight_layout()
    if out_png:
        plt.savefig(out_png, dpi=120)
    else:
        plt.show()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per_onu", required=True, help="CSV *_per_onu.csv")
    ap.add_argument("--cycles",  required=True, help="CSV *_cycles.csv")
    ap.add_argument("--outdir",  default="out")
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)
    plot_throughput_per_onu(args.per_onu, os.path.join(args.outdir, "throughput_per_onu.png"))
    plot_fairness_cycles(args.cycles,  os.path.join(args.outdir, "fairness_cycles.png"))
    plot_utilization_cycles(args.cycles, os.path.join(args.outdir, "utilization_cycles.png"))
    print("PNG creados en", args.outdir)

if __name__ == "__main__":
    main()
