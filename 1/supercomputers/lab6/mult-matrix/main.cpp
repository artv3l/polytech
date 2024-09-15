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

int mult(const std::vector<int>& a, const std::vector<int>& b)
{
    int result = 0;
    for (size_t i = 0, count = a.size(); i < count; i++) {
        result += a[i] * b[i];
    }
    return result;
}


int main(int argc, char** argv)
{
    auto getFileName = [](size_t process) -> std::string {
        std::ostringstream oss;
        oss << "../data_" << process << ".txt";
        return oss.str();
    };

    MPI_Init(&argc, &argv);
    int nProcesses = 0;
    MPI_Comm_size(MPI_COMM_WORLD, &nProcesses);
    int rank = 0;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);

    std::ifstream file(getFileName(rank));
    auto readElem = [&file]() {
        int elem = 0;
        file >> elem;
        return elem;
    };
    auto readVector = [&readElem](std::vector<int>& vector, std::vector<size_t>& indices) {
        indices.push_back(readElem());
        std::generate(vector.begin(), vector.end(), readElem);
    };

    // Читаем подготовленные данные
    size_t rowsBatch = 0, nRows = 0, nElems = 0;
    file >> rowsBatch >> nRows >> nElems;
    std::vector<std::vector<int>> rows(nRows, std::vector(nElems, 0));
    std::vector<size_t> rowIndices;
    for (auto& vec : rows)
        readVector(vec, rowIndices);

    size_t columnsBatch = 0,nColumns = 0;
    file >> columnsBatch >> nColumns;
    std::vector<std::vector<int>> columns(nColumns, std::vector(nElems, 0));
    std::vector<size_t> columnIndices;
    for (auto& vec : columns)
        readVector(vec, columnIndices);
    
    size_t res_n = 0, res_m = 0;
    file >> res_n >> res_m;

    // Результат - строки
    std::vector<std::vector<int>> result(res_n, std::vector(res_m, 0));

    for (size_t iRow = 0; iRow < rowsBatch; iRow++) {
        bool isRowExist = (iRow < nRows);
        const auto* row = isRowExist ? &rows[iRow] : nullptr;

        // Цикл по своим столбцам
        for (size_t i = 0; i < columnsBatch; i++) {
            

            bool isColumnExist = (i < nColumns);

            // Обрабатываемый столбец
            // В начале берем свой. Потом будет меняться в зависимости от того, что получили от соседей (не может быть nullptr)
            std::vector<int> buf(nElems, 0);
            auto* column = isColumnExist ? &columns[i] : &buf;

            // Реальный! Индекс столбца, который обрабатываем. В начале это свой. Потом передаем по кругу и получаем индекс соседей
            size_t iColumn = isColumnExist ? columnIndices[i] : 0;

            // Цикл по чужим столбцам. Передаем по кругу
            for (size_t j = 0; j < columnsBatch * nProcesses; j++) {
                if (row && isColumnExist) {
                    std::cout << "rank=" << rank << ", mult " << rowIndices[iRow] << " * " << iColumn << "\n";
                    result[rowIndices[iRow]][iColumn] = mult(*row, *column);
                }

                int nextRank = (rank + 1) % nProcesses; // Следующий процесс в кольце
                int prevRank = (rank - 1 + nProcesses) % nProcesses; // Предыдущий процесс в кольце

                MPI_Status status;
                int exist = static_cast<int>(isColumnExist);
                MPI_Sendrecv_replace(&exist, 1, MPI_INT, nextRank, 0, prevRank, 0, MPI_COMM_WORLD, &status);

                MPI_Sendrecv_replace(column->data(), nElems,
                                     MPI_INT, nextRank, iColumn, prevRank, MPI_ANY_TAG, MPI_COMM_WORLD, &status);
                iColumn = status.MPI_TAG;
                isColumnExist = exist;


            }
        }
    }

    std::cout << "res rank=" << rank << "\n";
    for (auto vec : result) {
        for (int v : vec) {
            std::cout << v << " ";
        }
        std::cout << "\n";
    }

    MPI_Finalize();

    return 0;
}
