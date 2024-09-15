#include <iostream>
#include <vector>
#include <string>
#include <array>
#include <algorithm>
#include <fstream>
#include <sstream>
#include <functional>

#include "mpi.h"

using Matrix = std::vector<std::vector<int>>;

int main(int argc, char** argv)
{
    auto getFileName = [](size_t process) -> std::string {
        std::ostringstream oss;
        oss << "../data_" << process << ".txt";
        return oss.str();
    };

    //Matrix result(a.size(), std::vector(b[0].size(), 0));

    //MPI_Init(&argc, &argv);
    const int nThreads = 0;
    //MPI_Comm_size(MPI_COMM_WORLD, const_cast<int*>(&nThreads));
    const int rank = 0;
    //MPI_Comm_rank(MPI_COMM_WORLD, const_cast<int*>(&rank));

    std::ifstream file(getFileName(rank));
    auto readElem = [&file]() {
        int elem = 0;
        file >> elem;
        return elem;
    };
    auto readVector = [&readElem](std::vector<int>& vector) {
        std::generate(vector.begin(), vector.end(), readElem);
    };

    size_t nColumns = 0, nElems = 0;
    file >> nColumns >> nElems;
    std::vector<std::vector<int>> columns(nColumns, std::vector(nElems, 0));
    std::for_each(columns.begin(), columns.end(), readVector);
    size_t nRows = 0;
    file >> nRows;
    std::vector<std::vector<int>> rows(nRows, std::vector(nElems, 0));
    std::for_each(rows.begin(), rows.end(), readVector);




    //MPI_Finalize();

    return 0;
}
