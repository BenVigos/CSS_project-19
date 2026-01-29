from simulations.drosselschwab import simulate_drosselschwab_record

fires, grid, records = simulate_drosselschwab_record(L=64, p=0.01, f=0.001, steps=20, suppress=10)
print('len(fires)=', len(fires))
print('fires sample:', fires[:30])
print('num steps in records=', len(records))
nonempty_steps = [r for r in records if r['fires']]
print('steps with fires:', len(nonempty_steps))
for r in nonempty_steps:
    print('step', r['step'], 'fires', r['fires'])
