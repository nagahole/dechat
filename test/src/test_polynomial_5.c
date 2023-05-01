#include <stdio.h>
#include "test.h"
#include "polynomial.h"
#include "test_polynomial.h"


#define POLY_MANY 1025

int main()
{
    test_polynomial();
    return 0;
}

int test_polynomial()
{
    const float tolerance = 1E-5;
    const float values[] = {-1};

    char poly[SIZEOF_POLYNOMIAL(POLY_MANY)];

    float elements[POLY_MANY] = {0};
    for (int i = 0; i < POLY_MANY; i++)
    {
        elements[i] = (2 * (i % 2)) - 1;
    }

    polynomial_create(poly, POLY_MANY, elements);

    for (int t = 0; t < 1; t++)
    {    
        float res = (values[t] - polynomial_evaluate(poly, t));
        assert(res * res < tolerance); 
    }
    return 0;
}



