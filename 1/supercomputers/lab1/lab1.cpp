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

int main(int argc, char** argv)
{
	//lab1::example1();
	//lab1::task5();

	lab2::task7();

	return 0;
}
