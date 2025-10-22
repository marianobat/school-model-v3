from simulate_case import Params, simulate

p = Params()
df, _ = simulate(p)
print(df.head().to_string(index=False))
