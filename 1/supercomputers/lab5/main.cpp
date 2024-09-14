#include <iostream>
#include <vector>
#include <string>
#include <array>
#include <algorithm>

#include "mpi.h"



int main(int argc, char** argv)
{
    constexpr size_t c_count = 8; // ƒолжно быть равно кол-ву процессов, на котором запускаетс€ приложение
    const std::vector<int> c_data(c_count - 1, 123);

    MPI_Init(&argc, &argv);

    int rank = 0;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);

    if (rank == 0) {
        double start = MPI_Wtime();
        for (size_t i = 0; i < c_count - 1; i++) {
            int num = c_data[i];
            MPI_Send(&num, 1, MPI_INT, i + 1, 0, MPI_COMM_WORLD);
        }
        double time = MPI_Wtime() - start;
        std::cout << "rank=0, send    time = " << time << "\n";

    } else {
        int recv = 0;
        MPI_Status status;

        double start = MPI_Wtime();
        MPI_Recv(&recv, 1, MPI_INT, 0, 0, MPI_COMM_WORLD, &status);
        double time = MPI_Wtime() - start;
        std::cout << "rank=" << rank << ", recv    time = " << time << "\n";
    }

    int recv = 0;

    double start = MPI_Wtime();
    MPI_Scatter(c_data.data(), 1, MPI_INT, &recv, 1, MPI_INT, 0, MPI_COMM_WORLD);
    double time = MPI_Wtime() - start;
    std::cout << "rank=" << rank << ", scatter time = " << time << "\n";

    MPI_Finalize();

    return 0;
}
