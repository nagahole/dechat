#include <stdio.h>
#include "test.h"
#include "polynomial.h"
#include "test_polynomial.h"

int main()
{

    test_polynomial();
    return 0;
}

int test_polynomial()
{
    const float value = 1;
    const float tolerance = 1E-5;

    char poly[SIZEOF_POLYNOMIAL(1)];
    float elements[1] = {value};
    polynomial_create(poly, 1, elements);
    for (int t = 0; t < 10; t++)
    {    
        float res = (value - polynomial_evaluate(poly, t));
        assert(res * res < tolerance); 
    }
    return 0;
}


