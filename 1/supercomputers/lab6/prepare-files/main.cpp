#include <iostream>
#include <vector>
#include <string>
#include <array>
#include <algorithm>
#include <fstream>
#include <sstream>
#include <functional>

using Matrix = std::vector<std::vector<int>>;

void prepareFiles(const Matrix& a, const Matrix& b, size_t nProcesses, std::function<std::ofstream(size_t)> getFile)
{
    for (size_t iProcess = 0; iProcess < nProcesses; iProcess++) {
        std::ofstream& file = getFile(iProcess);

        // Максимальное кол-во строк в каком-либо из процессов. Нужно чтобы можно было передавать даные по кругу
        // (Хотя для строк мб это и не нужно...)
        size_t aRowsBatchCount = (a.size() / nProcesses) + static_cast<size_t>(a.size() % nProcesses != 0);

        // Кол-во строк для конкретно этого процесса. Столько строк будет записано в файл далее
        size_t aRowsCount = (a.size() / nProcesses) + static_cast<size_t>(iProcess < a.size() % nProcesses);

        // a[0].size() - Кол-во элементов в строке
        file << aRowsBatchCount << " " << aRowsCount << " " << a[0].size() << "\n";

        size_t iRow = iProcess;
        while (iRow < a.size()) {
            // Реальный индекс строки во всей результирующей матрице. Нужно для сбора результатов и объединения их в одну итоговую матрицу
            file << iRow << " "; 

            // Элементы строки
            std::copy(a[iRow].cbegin(), a[iRow].cend(), std::ostream_iterator<int>(file, " "));
            file << "\n";
            iRow += nProcesses;
        }

        // Для столбцов аналогично, только не пишем кол-во элементов в столбце. Оно всегда равно кол-ву элементов в строке

        size_t bColumnsBatchCount = (b[0].size() / nProcesses) + static_cast<size_t>(b[0].size() % nProcesses != 0);
        size_t bColumnsCount = (b[0].size() / nProcesses) + static_cast<size_t>(iProcess < b[0].size() % nProcesses);
        file << bColumnsBatchCount << " " << bColumnsCount << "\n";
        size_t iColumn = iProcess;
        while (iColumn < b[0].size()) {
            file << iColumn << " ";
            for (size_t j = 0, count = b.size(); j < count; j++) {
                file << b[j][iColumn] << " ";
            }
            file << "\n";
            iColumn += nProcesses;
        }

        // Размер итоговой матрицы
        file << a.size() << " " << b[0].size() << "\n";
    }
}

int main(int argc, char** argv)
{
    const Matrix a = {
        {1, 2, 3, -7, 7, -4},
        {5, -2, 7, 1, 15, 1},
        {-1, 9, 0, 4, 0, -9},
        {8, 3, -5, 5, 2, 3},
        {88, 3, 2, -15, 0, 1}
    };
    const Matrix b = {
        {1, 2, -6, 4, 4},
        {5, 6, 2, 2, -8},
        {-4, 2, 0, 3, 3},
        {2, 9, 4, 1, 0},
        {8, 2, -9, 0, 3},
        {0, 3, 5, 6, -6}
    };
    
    auto getFile = [](size_t process) -> std::ofstream {
        std::ostringstream oss;
        oss << "../data_" << process << ".txt";
        return std::ofstream(oss.str());
    };

    prepareFiles(a, b, 4, getFile);

    return 0;
}
