#include <iostream>
#include <array>
#include <random>
#include <utility>
#include <algorithm>
#include <list>
#include <iterator>
#include <cmath>

#include <omp.h>

namespace
{
bool isSimpleNumber(int number)
{
	bool isSimple = true;
	for (int i = 2; i < number; i++) {
		if (number % i == 0) {
			isSimple = false;
			break;
		}
	}
	return isSimple;
}
}

namespace lab1
{
void example1()
{
	const int c_maxThreads = omp_get_max_threads();
	std::cout << "Max threads: " << c_maxThreads << "\n";

	int nThreads = c_maxThreads > 4 ? 4 : c_maxThreads;

	#pragma omp parallel num_threads(nThreads)
	{
		int count = omp_get_num_threads();
		int currentThread = omp_get_thread_num();

		#pragma omp critical (cout)
		{
			std::cout << "Hello, OpenMP! I am " << currentThread << " of " << count << "\n";
		}
	}
}

void task5()
{
	constexpr size_t c_nNumbers = 100;
	constexpr std::pair<int, int> c_range(1, 50);

	std::array<int, c_nNumbers> numbers = {};

	// Ќужно дл€ генерации случайных чисел
	std::random_device dev;
	std::mt19937 rng(dev());
	std::uniform_int_distribution<std::mt19937::result_type> dist(c_range.first, c_range.second);
	auto generateNumber = [&dist, &rng]() {
		return dist(rng);
		};

	// √енерируем случайные натуральные числа и заполн€ем массив
	std::generate(numbers.begin(), numbers.end(), generateNumber);

	std::list<int> simpleNumbers;

	/*
		ƒинамическое планирование - т.к. дл€ разных чисел врем€ вычислений может сильно отличатьс€
		shared - —овместное использование переменных между потоками
	*/
	#pragma omp parallel for schedule(dynamic) shared(numbers, simpleNumbers)
	for (int i = 0; i < numbers.size(); i++) {
		const int number = numbers.at(i);
		if (isSimpleNumber(number)) {
			#pragma omp critical (push_back)
			{
				simpleNumbers.push_back(number);
			}
		}
	}

	std::cout << "numbers: ";
	std::copy(numbers.cbegin(), numbers.cend(), std::ostream_iterator<int>(std::cout, ", "));
	std::cout << "\nsimpleNumbers: ";
	std::copy(simpleNumbers.cbegin(), simpleNumbers.cend(), std::ostream_iterator<int>(std::cout, ", "));

}
}

namespace lab2
{
void task7()
{
	constexpr int N = 5;

	double a[N];
	double y, x;
	# pragma omp parallel for private(x, y)
	for (int i = 0; i < N; i++)
	{
		double iDbl = static_cast<double>(i);
		y = iDbl * std::sin(iDbl / N * 3.14);
		x = iDbl * std::cos(iDbl / N * 3.14);
		a[i] = y + x;
	}

	std::copy(std::begin(a), std::end(a), std::ostream_iterator<int>(std::cout, ", "));
}
}

namespace lab3
{
void task5()
{
	const size_t nThreads = omp_get_max_threads();
	constexpr size_t N = 5;
	constexpr std::pair<int, int> c_range(1, 4);

	std::random_device dev;
	std::mt19937 rng(dev());
	std::uniform_int_distribution<std::mt19937::result_type> dist(c_range.first, c_range.second);
	auto generateNumber = [&dist, &rng]() {
		return dist(rng);
		};

	std::array<std::array<double, N>, N> matrix;
	matrix[0] = { 1, 1, 1, 1, 0 };
	matrix[1] = { 1, 2, 1, 1, 0 };
	matrix[2] = { 1, 1, 3, 1, 0 };
	matrix[3] = { 1, 1, 1, 4, 0 };
	matrix[4] = { 1, 2, 3, 4, 0 };

	/*for (size_t i = 0; i < N; i++)
		for (size_t j = 0; j < N; j++)
			matrix[i][j] = generateNumber();*/


	for (size_t i = 0; i < N; i++)
	{
		std::copy(matrix[i].cbegin(), matrix[i].cend(), std::ostream_iterator<int>(std::cout, ", "));
		std::cout << "\n";
	}

	const double EPS = 1E-9;

	int rank = N;
	std::vector<bool> line_used(N);
	for (int i = 0; i < N; i++) {
		int j = 0;

		for (j = 0; j < N; j++)
			if (!line_used[j] && abs(matrix[j][i]) > EPS)
				break;

		if (j == N)
		{
			rank--;
		}
		else {
			line_used[j] = true;

			#pragma omp parallel for
			for (int p = i + 1; p < N; p++)
				matrix[j][p] /= matrix[j][i];

			for (int k = 0; k < N; k++)
			{
				if (k != j && abs(matrix[k][i]) > EPS)
				{
					#pragma omp parallel for
					for (int p = i + 1; p < N; ++p)
						matrix[k][p] -= matrix[j][p] * matrix[k][i];
				}
			}
		}
	}

	std::cout << "rank = " << rank << "\n";

}
}

int main(int argc, char** argv)
{
	//lab1::example1();
	//lab1::task5();

	//lab2::task7();

	lab3::task5();

	return 0;
}
