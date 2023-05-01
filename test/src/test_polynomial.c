#include <stdio.h>
#include "test.h"
#include "polynomial.h"
#include "test_polynomial.h"


int main()
{

    test_monic();
    test_linear();
    test_quadratic();
    return 0;
}

int test_monic()
{
    const float value = 1;
    const float tolerance = 1E-5;

    void* poly[SIZEOF_POLYNOMIAL(1)];
    float elements[1] = {value};
    polynomial_create(poly, 1, elements);
    for (int t = 0; t < 10; t++)
    {    
        float res = (value - polynomial_evaluate(poly, t));
        DEBUG_PRINT("%f\n", res);
        assert(res * res < tolerance); 
    }
    return 0;
}

#define N_TESTS_LINEAR 10
#define POLY_LINEAR 2
int test_linear()
{
    const float values[N_TESTS_LINEAR] = {1000, 998, 996, 994, 992, 990, 988, 986, 984, 982};
    const float tolerance = 1E-5;

    void* poly[SIZEOF_POLYNOMIAL(POLY_LINEAR)];
    float elements[POLY_LINEAR] = {-2, 1000};
    polynomial_create(poly, POLY_LINEAR, elements);
    for (int t = 0; t < N_TESTS_LINEAR; t++)
    {    
        float res = (values[t] - polynomial_evaluate(poly, t));
        DEBUG_PRINT("Diff %f\n", res);
        DEBUG_PRINT("Val %f\n", polynomial_evaluate(poly, t));
        assert(res * res < tolerance); 
    }
    return 0;
}

#define POLY_QUAD 3
int test_quadratic()
{
    const float values[10] = {1000, 998, 994, 988, 980, 970, 958, 944, 928, 910};
    const float tolerance = 1E-5;

    void* poly[SIZEOF_POLYNOMIAL(POLY_QUAD)];
    float elements[POLY_QUAD] = {-1, -1, 1000};
    polynomial_create(poly, POLY_QUAD, elements);
    for (int t = 0; t < 10; t++)
    {    
        float res = (values[t] - polynomial_evaluate(poly, t));
        DEBUG_PRINT("%f\n", res);
        assert(res * res < tolerance); 
    }
    return 0;
}
