#include <stdio.h>

int main() {
    int n, tq;

    printf("Enter number of processes: ");
    scanf("%d", &n);

    int bt[n], rt[n], wt[n], tat[n];

    // Input burst times
    for (int i = 0; i < n; i++) {
        printf("Enter burst time for process %d: ", i + 1);
        scanf("%d", &bt[i]);
        rt[i] = bt[i]; // remaining time = burst time
    }

    printf("Enter time quantum: ");
    scanf("%d", &tq);

    int time = 0, done;

    do {
        done = 1;

        for (int i = 0; i < n; i++) {
            if (rt[i] > 0) {
                done = 0;

                if (rt[i] > tq) {
                    time += tq;
                    rt[i] -= tq;
                } else {
                    time += rt[i];
                    wt[i] = time - bt[i]; // waiting time
                    rt[i] = 0;
                }
            }
        }
    } while (!done);

    // Calculate Turnaround Time
    for (int i = 0; i < n; i++) {
        tat[i] = bt[i] + wt[i];
    }

    // Output
    printf("\nProcess\tBT\tWT\tTAT\n");
    for (int i = 0; i < n; i++) {
        printf("P%d\t%d\t%d\t%d\n", i + 1, bt[i], wt[i], tat[i]);
    }

    return 0;
}
