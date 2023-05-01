#include <stdio.h>
#include "test.h"
#include "polynomial.h"
#include "test_polynomial.h"


#define POLY_QUAD 3

int main()
{
    test_polynomial();
    return 0;
}


void poly_create(void* poly)
{
    float elements[POLY_QUAD] = {-1, -1, 1000};
    polynomial_create(poly, POLY_QUAD, elements);
}


// This function just exists to occupy stack space
int stack_occupier(int i)
{
    int x[100] = {0};
    for (int j = 0; j <= i; j++)
    {
        j += j;
        i -= j;
    }
    return i;
}

int test_polynomial()
{
    const float values[10] = {1000, 998, 994, 988, 980, 970, 958, 944, 928, 910};
    const float tolerance = 1E-5;

    char poly[SIZEOF_POLYNOMIAL(POLY_QUAD)];

    poly_create(poly);
    int i = stack_occupier(5);
    i -= 1;

    for (int t = 0; t < 10; t++)
    {    
        float res = (values[t] - polynomial_evaluate(poly, t));
        assert(res * res < tolerance); 
    }
    return 0;
}



