#include <iostream>
#include <vector>
#include <string>
#include <array>
#include <algorithm>

#include "mpi.h"

std::vector<std::string> splitString(const std::string& input, int n)
{
    std::vector<std::string> parts;
    int length = input.length();
    int partSize = length / n;
    for (int i = 0; i < n; i++) {
        int start = partSize * i;
        int current_part_size = partSize;
        if (i == n - 1) {
            current_part_size += length % n;
        }
        parts.push_back(input.substr(start, current_part_size));
    }
    return parts;
}

int main(int argc, char** argv)
{
    constexpr size_t c_count = 4; // ������ ���� ����� ���-�� ���������, �� ������� ����������� ����������
    constexpr std::array<int, c_count> c_key = {1, 2, -3, 0};
    const std::string c_message = "hello world mpi";

    auto decode = [](const std::string & str, int key) -> std::string {
        std::string result = str;
        std::for_each(result.begin(), result.end(), [key](char& c) {
            c = c - key;
        });
        return result;
    };

    MPI_Init(&argc, &argv);

    int rank = 0;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);

    if (rank == 0) {
        // ������� ������� - 0. ��������� ��������� (������) ��������� ���������
        // ������� ������� ����� ���� �� ���������� ������ ����� ���������
        
        // ��������� ������ �� �����
        auto parts = splitString(c_message, c_count);
        std::cout << "input= ";
        std::copy(parts.cbegin(), parts.cend(), std::ostream_iterator<std::string>(std::cout, ";"));
        std::cout << "\n";

        // �������� ����� � ������� �����
        for (size_t i = 0, count = parts.size(); i < count; i++) {
            std::for_each(parts[i].begin(), parts[i].end(), [&c_key, i](char& c) {
                c = c + c_key[i];
            });
        }
        std::cout << "encoded= ";
        std::copy(parts.cbegin(), parts.cend(), std::ostream_iterator<std::string>(std::cout, ";"));
        std::cout << "\n";

        // ��������� ������ ��������� ����� ���������, ������� �� ���������� ������������
        for (size_t i = 1; i < c_count; i++) {
            int length = parts[i].length();
            MPI_Send(&length, 1, MPI_INT, i, 0, MPI_COMM_WORLD); // ���������� ����� ��������� (tag = 0)
            MPI_Send(parts[i].c_str(), parts[i].length(), MPI_CHAR, i, 1, MPI_COMM_WORLD); // ���������� ��������� (tag = 1)
        }

        // ����������� ���� ����� ���������
        std::string decoded = decode(parts[0], c_key[rank]);
        std::cout << "rank=" << rank << ", recieved=" << parts[0] << ", decoded=" << decoded << "\n";

        // ��������� - �������������� ��������� �� ������
        std::vector<std::string> result(c_count);
        result[0] = decoded;

        // ��������� ��������� �� ������ ���������
        for (size_t i = 1; i < c_count; i++) {
            MPI_Status status;

            int length = 0;
            MPI_Recv(&length, 1, MPI_INT, MPI_ANY_SOURCE, 0, MPI_COMM_WORLD, &status);

            std::string msg(length, '\0');
            MPI_Recv(msg.data(), length, MPI_CHAR, status.MPI_SOURCE, 1, MPI_COMM_WORLD, &status);

            result[status.MPI_SOURCE] = msg;
        }

        // ������� ���������
        std::cout << "result=";
        for (std::string i : result) {
            std::cout << i;
        }

    } else {
        // ��������� ��������� � �������, ������� ����� ������������

        MPI_Status status;

        // ��������� ����� ���������
        int length = 0;
        MPI_Recv(&length, 1, MPI_INT, 0, 0, MPI_COMM_WORLD, &status);

        // ��������� ���������
        std::string msg(length, '\0');
        MPI_Recv(msg.data(), length, MPI_CHAR, 0, 1, MPI_COMM_WORLD, &status);

        // ��������������
        std::string decoded = decode(msg, c_key[rank]);
        std::cout << "rank=" << rank << ", recieved=" << msg << ", decoded=" << decoded << "\n";

        // ���������� ��������� � ������� �������
        MPI_Send(&length, 1, MPI_INT, 0, 0, MPI_COMM_WORLD);
        MPI_Send(decoded.c_str(), decoded.length(), MPI_CHAR, 0, 1, MPI_COMM_WORLD);
    }

    MPI_Finalize();

    return 0;
}
