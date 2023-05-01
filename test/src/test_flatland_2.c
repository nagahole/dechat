#include "test_flatland.h"

int main()
{
    flatland_linear();
    return 0;
}

#define POLY_SIZE 2
#define N_AST 1
#define TOLERANCE 1
#define N_SCANNER_POSITIONS 3
void flatland_linear()
{
    // Create cluster object
    char cluster[SIZEOF_ASTEROID_CLUSTER(N_AST)];
    asteroid_cluster_create(cluster, N_AST, TOLERANCE); 

    // Create Polynomial
    char poly[SIZEOF_POLYNOMIAL(POLY_SIZE)];
    float poly_vals[POLY_SIZE] = {-50, 1001};
    polynomial_create(poly, POLY_SIZE, poly_vals);

    // Add asteroid to cluster
    asteroid_cluster_add_asteroid(cluster, poly, poly); 

    // Create the scanner
    char scanner[SIZEOF_SCANNER(N_SCANNER_POSITIONS)];
    float scanner_pos[N_SCANNER_POSITIONS] = {0, 200, 400}; 
    scanner_create(scanner, N_SCANNER_POSITIONS, scanner_pos); 

    assert(0 == asteroid_cluster_clear(cluster));
    
    flatland_protect(cluster, scanner);
    
    assert(0 == asteroid_cluster_impact(cluster)); 
    assert(1 == asteroid_cluster_clear(cluster));

    return;
}
