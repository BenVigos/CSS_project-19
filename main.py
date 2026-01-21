from src.rq1 import run_simulation

def main():
    fire_data, final_grid = run_simulation(L=10, p=0.05, f=0.001, steps=500)
    print(fire_data, final_grid.shape)


if __name__ == "__main__":
    main()
