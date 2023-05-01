#include <stdio.h>
#include "test.h"
#include "polynomial.h"
#include "test_polynomial.h"


int main()
{
    test_polynomial();
    return 0;
}

#define N_TESTS_LINEAR 10
#define POLY_LINEAR 2
int test_polynomial()
{
    const float values[N_TESTS_LINEAR] = {1000, 998, 996, 994, 992, 990, 988, 986, 984, 982};
    const float tolerance = 1E-5;

    char poly[SIZEOF_POLYNOMIAL(POLY_LINEAR)];
    float elements[POLY_LINEAR] = {-2, 1000};
    polynomial_create(poly, POLY_LINEAR, elements);
    for (int t = 0; t < N_TESTS_LINEAR; t++)
    {    
        float res = (values[t] - polynomial_evaluate(poly, t));
        assert(res * res < tolerance); 
    }
    return 0;
}

