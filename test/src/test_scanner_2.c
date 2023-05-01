#include "test_scanner.h"

#define STATIC_POLY 1
#define STATIC_N_AST 1
#define TOLERANCE 1
#define N_SCANNER_POSITIONS_STATIC_TEST 5

int main()
{
    test_scan_static();
    return 0;
}

void test_scan_static()
{
    // Asteroid sits at (100, 100) forever
    // Create cluster object
    char cluster[SIZEOF_ASTEROID_CLUSTER(STATIC_N_AST)];
    asteroid_cluster_create(cluster, STATIC_N_AST, TOLERANCE); 

    // Create Polynomial
    char poly[SIZEOF_POLYNOMIAL(STATIC_POLY)];
    float poly_vals[STATIC_POLY] = {100};
    polynomial_create(poly, STATIC_POLY, poly_vals);
   
    // Add asteroid to cluster
    // Use previously created polynomial
    asteroid_cluster_add_asteroid(cluster, poly, poly); 
    assert(0 == asteroid_cluster_clear(cluster));
 
    // Create the scanner
    char scanner[SIZEOF_SCANNER(N_SCANNER_POSITIONS_STATIC_TEST)];
    float scanner_pos[N_SCANNER_POSITIONS_STATIC_TEST] = {0, 50, 100, 150, 200}; 
    scanner_create(scanner, N_SCANNER_POSITIONS_STATIC_TEST, scanner_pos); 

    // Scan
    float* dist = scan(scanner, cluster);
   
    // Check the output 
    assert(FLOAT_CMP(dist[0], 141, TOLERANCE));
    assert(FLOAT_CMP(dist[1], 111, TOLERANCE));
    assert(FLOAT_CMP(dist[2], 100, TOLERANCE));
    assert(FLOAT_CMP(dist[3], 111, TOLERANCE));
    assert(FLOAT_CMP(dist[4], 141, TOLERANCE));

    return;
}
