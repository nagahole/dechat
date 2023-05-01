#include "test_flatland.h"

int main()
{
    flatland_vertical();
    return 0;
}

#define POLY_SIZE_Y 2
#define POLY_SIZE_X 1
#define N_AST 1
#define TOLERANCE 1
#define N_SCANNER_POSITIONS 3
void flatland_vertical()
{
    // Create cluster object
    char cluster[SIZEOF_ASTEROID_CLUSTER(N_AST)];
    asteroid_cluster_create(cluster, N_AST, TOLERANCE); 

    // Create Polynomial
    char poly_x[SIZEOF_POLYNOMIAL(POLY_SIZE_X)];
    char poly_y[SIZEOF_POLYNOMIAL(POLY_SIZE_Y)];
    float poly_vals_x[POLY_SIZE_X] = {100};
    float poly_vals_y[POLY_SIZE_Y] = {-50, 1001};

    polynomial_create(poly_x, POLY_SIZE_X, poly_vals_x);
    polynomial_create(poly_y, POLY_SIZE_Y, poly_vals_y);

    // Add asteroid to cluster
    asteroid_cluster_add_asteroid(cluster, poly_x, poly_y); 

    // Create the scanner
    char scanner[SIZEOF_SCANNER(N_SCANNER_POSITIONS)];
    float scanner_pos[N_SCANNER_POSITIONS] = {0, 200, 300}; 
    scanner_create(scanner, N_SCANNER_POSITIONS, scanner_pos); 

    assert(0 == asteroid_cluster_clear(cluster));
    
    flatland_protect(cluster, scanner);
    
    assert(0 == asteroid_cluster_impact(cluster)); 
    assert(1 == asteroid_cluster_clear(cluster));

    return;
}
