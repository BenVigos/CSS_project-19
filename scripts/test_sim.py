from simulations.drosselschwab import simulate_drosselschwab_record

if __name__ == '__main__':
    fires, grid, records = simulate_drosselschwab_record(L=32, p=0.01, f=0.001, steps=10, suppress=2)
    print('fires len:', len(fires))
    print('records len:', len(records))
    print('first record:', records[0] if records else None)
