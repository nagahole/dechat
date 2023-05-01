#include "test_asteroid.h"

int main()
{
    test_asteroid_linear();
    return 0;
}

#define TOLERANCE 1
#define LINEAR_POLY 2
#define LINEAR_N_AST 1
void test_asteroid_linear()
{
    // Asteroid sits at (100, 100) forever
    // Create cluster object
    char data[SIZEOF_ASTEROID_CLUSTER(LINEAR_N_AST)];
    asteroid_cluster_create(data, LINEAR_N_AST, TOLERANCE); 
    // Create Polynomial
    char poly[SIZEOF_POLYNOMIAL(2)];
    float poly_vals[LINEAR_POLY] = {-3, 100};
    polynomial_create(poly, LINEAR_POLY, poly_vals);
   
    // Add asteroid to cluster
    asteroid_cluster_add_asteroid(data, poly, poly); 
    assert(0 == asteroid_cluster_clear(data));
 
    asteroid_cluster_update(data); 
    // Scan should be at 97
    float dist = asteroid_cluster_scan(data, 0, 97);
    assert(FLOAT_CMP(dist, 97, TOLERANCE));

    // Try to shoot asteroid down, and miss
    // As scan should have updated the position
    // 97 Should miss as the asteroid should be at 94
    asteroid_cluster_intercept(data, 97, 97);
    assert(0 == asteroid_cluster_clear(data));

    // Try to shoot asteroid down, and hit
    asteroid_cluster_intercept(data, 91, 91);
    assert(1 == asteroid_cluster_clear(data));
    return;
}
