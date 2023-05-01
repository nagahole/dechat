#include "test_asteroid.h"

int main()
{
    test_asteroid_lots();
    return 0;
}

#define TOLERANCE 1
#define LINEAR_POLY 2
#define N_AST 1025
void test_asteroid_lots()
{
    // Create cluster object
    char cluster[SIZEOF_ASTEROID_CLUSTER(N_AST)];
    asteroid_cluster_create(cluster, N_AST, TOLERANCE); 

    // Create Polynomial
    char poly[SIZEOF_POLYNOMIAL(2)];
    float poly_vals[LINEAR_POLY] = {-3, 1};
    polynomial_create(poly, LINEAR_POLY, poly_vals);
   
    // Add asteroid to cluster
    for (int i = 0; i < N_AST; i++)
    {
        asteroid_cluster_add_asteroid(cluster, poly, poly); 
    }
    assert(0 == asteroid_cluster_clear(cluster));
 
    asteroid_cluster_update(cluster); 
    
    assert(0 == asteroid_cluster_clear(cluster));
    assert(1 == asteroid_cluster_impact(cluster));

    return;
}
