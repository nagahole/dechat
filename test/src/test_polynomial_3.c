#include <stdio.h>
#include "test.h"
#include "polynomial.h"
#include "test_polynomial.h"


int main()
{

    test_polynomial();
    return 0;
}

#define POLY_QUAD 3
int test_polynomial()
{
    const float values[10] = {1000, 998, 994, 988, 980, 970, 958, 944, 928, 910};
    const float tolerance = 1E-5;

    char poly[SIZEOF_POLYNOMIAL(POLY_QUAD)];
    float elements[POLY_QUAD] = {-1, -1, 1000};
    polynomial_create(poly, POLY_QUAD, elements);
    for (int t = 0; t < 10; t++)
    {    
        float res = (values[t] - polynomial_evaluate(poly, t));
        assert(res * res < tolerance); 
    }
    return 0;
}
