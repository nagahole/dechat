#ifndef POLYNOMIAL_H
#define POLYNOMIAL_H 1

// Defines the number of bytes needed to store a polynomial containing n_elements
#define SIZEOF_POLYNOMIAL(n_elements) (1) // TODO


/* polynomial_create
 * Instantiates a new polynomial object
 * :: void* data      :: A pointer to the location to instantiate
 * :: int n_elements  :: The number of elements in the polynomial
 * :: float* elements :: A pointer to the polynomial coefficients
 * Acts in place on data 
 */
void polynomial_create(
        void* data,
        int n_elements,
        float* elements);

/*
 * polynomial_evaluate
 * Evaluates the polynomial at some time t
 * :: void* poly :: Pointer to a polynomial object
 * :: int time   :: The time at which to evaluate the polynomial
 * Returns the evaluation of the polynomial
 */
float polynomial_evaluate(void* poly, int time);

#endif
