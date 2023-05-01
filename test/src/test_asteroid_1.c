#include "test_asteroid.h"

int main()
{
    test_asteroid_static();
    return 0;
}

#define STATIC_POLY 1
#define STATIC_N_AST 1
#define TOLERANCE 1
void test_asteroid_static()
{
    // Asteroid sits at (100, 100) forever
    // Create cluster object
    char data[SIZEOF_ASTEROID_CLUSTER(STATIC_N_AST)];
    asteroid_cluster_create(data, STATIC_N_AST, TOLERANCE); 

    // Create Polynomial
    char poly[SIZEOF_POLYNOMIAL(1)];
    float poly_vals[STATIC_POLY] = {100};
    polynomial_create(poly, STATIC_POLY, poly_vals);

    // Add asteroid to cluster
    asteroid_cluster_add_asteroid(data, poly, poly); 

    assert(0 == asteroid_cluster_clear(data));
   
    float dist = asteroid_cluster_scan(data, 0, 100);

    assert(FLOAT_CMP(dist, 100.0, TOLERANCE));

    // A second update should do nothing here
    // If it does then the shot later on should miss
    asteroid_cluster_update(data);

    // Update and rescan
    dist = asteroid_cluster_scan(data, 0, 100);
    asteroid_cluster_update(data);
    assert(FLOAT_CMP(dist, 100.0, TOLERANCE));

    // Try to shoot asteroid down
    asteroid_cluster_intercept(data, 100, 100);
    

    assert(1 == asteroid_cluster_clear(data));
    return;
}
