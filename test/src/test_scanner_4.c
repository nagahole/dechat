#include "test_scanner.h"
#define STATIC_POLY 1
#define STATIC_N_AST 1
#define TOLERANCE 1


int main()
{
    test_scanner_impact();
    return 0;
}

#define N_SCANNER_POSITIONS 5
void test_scanner_impact()
{
// Asteroid sits at (100, 1001) forever
    // Create cluster object
    char cluster[SIZEOF_ASTEROID_CLUSTER(STATIC_N_AST)];
    asteroid_cluster_create(cluster, STATIC_N_AST, TOLERANCE); 

    // Create Polynomial
    char poly_x[SIZEOF_POLYNOMIAL(STATIC_POLY)];
    char poly_y[SIZEOF_POLYNOMIAL(STATIC_POLY)];
    float poly_vals_x[STATIC_POLY] = {100};
    float poly_vals_y[STATIC_POLY] = {-1}; // We start with impact
    polynomial_create(poly_x, STATIC_POLY, poly_vals_x);
    polynomial_create(poly_y, STATIC_POLY, poly_vals_y);
   
    // Add asteroid to cluster
    // Use previously created polynomial
    asteroid_cluster_add_asteroid(cluster, poly_x, poly_y); 
    assert(0 == asteroid_cluster_clear(cluster));
 
    // Create the scanner
    char scanner[SIZEOF_SCANNER(N_SCANNER_POSITIONS)];
    float scanner_pos[N_SCANNER_POSITIONS] = {0, 50, 100, 150, 200}; 
    scanner_create(scanner, N_SCANNER_POSITIONS, scanner_pos); 

    // Scan
    float* dist = scan(scanner, cluster);
   
    // Check the output 
    for (int i = 0; i < N_SCANNER_POSITIONS; i++)
    {
        assert(isnan(dist[i]));
    }
    return;
}
