#include "test_flatland.h"

int main()
{
    flatland_static();
    return 0;
}

#define STATIC_POLY 1
#define STATIC_N_AST 1
#define TOLERANCE 1
#define N_SCANNER_POSITIONS_STATIC_TEST 5
void flatland_static()
{
    // Asteroid sits at (100, 100) forever
    // Create cluster object
    char cluster[SIZEOF_ASTEROID_CLUSTER(STATIC_N_AST)];
    asteroid_cluster_create(cluster, STATIC_N_AST, TOLERANCE); 

    // Create Polynomial
    char poly[SIZEOF_POLYNOMIAL(1)];
    float poly_vals[STATIC_POLY] = {100};
    polynomial_create(poly, STATIC_POLY, poly_vals);

    // Add asteroid to cluster
    asteroid_cluster_add_asteroid(cluster, poly, poly); 

    // Create the scanner
    char scanner[SIZEOF_SCANNER(N_SCANNER_POSITIONS_STATIC_TEST)];
    float scanner_pos[N_SCANNER_POSITIONS_STATIC_TEST] = {0, 50, 100, 150, 200}; 
    scanner_create(scanner, N_SCANNER_POSITIONS_STATIC_TEST, scanner_pos); 

    assert(0 == asteroid_cluster_clear(cluster));
    
    flatland_protect(cluster, scanner);
    
    assert(0 == asteroid_cluster_impact(cluster)); 

    assert(1 == asteroid_cluster_clear(cluster));
    return;
}
