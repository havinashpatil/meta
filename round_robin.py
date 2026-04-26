def round_robin(bt, tq):
    n = len(bt)
    rt = bt[:]
    wt = [0] * n
    tat = [0] * n

    time = 0
    done = False

    while not done:
        done = True
        for i in range(n):
            if rt[i] > 0:
                done = False
                if rt[i] > tq:
                    time += tq
                    rt[i] -= tq
                else:
                    time += rt[i]
                    wt[i] = time - bt[i]
                    rt[i] = 0

    for i in range(n):
        tat[i] = bt[i] + wt[i]

    return wt, tat


def main():
    n = int(input("Enter number of processes: "))
    if n <= 0:
        print("Number of processes must be > 0")
        return

    bt = []
    for i in range(n):
        bt_i = int(input(f"Enter burst time for process {i + 1}: "))
        if bt_i < 0:
            print("Burst time cannot be negative")
            return
        bt.append(bt_i)

    tq = int(input("Enter time quantum: "))
    if tq <= 0:
        print("Time quantum must be > 0")
        return

    wt, tat = round_robin(bt, tq)

    print("\nProcess\tBT\tWT\tTAT")
    for i in range(n):
        print(f"P{i + 1}\t{bt[i]}\t{wt[i]}\t{tat[i]}")


if __name__ == "__main__":
    main()
