#include "test_scanner.h"

int main()
{
    test_scanner_constructor();
    test_scan_static();
    return 0;
}

#define N_SCANNER_POSITIONS_CONSTRUCTOR_TEST 100
void test_scanner_constructor()
{
    float pos[N_SCANNER_POSITIONS_CONSTRUCTOR_TEST];
    for (int i = 0; i < N_SCANNER_POSITIONS_CONSTRUCTOR_TEST; i++)
    {
        pos[i] = i * i;
    }

    char scanner[SIZEOF_SCANNER(N_SCANNER_POSITIONS_CONSTRUCTOR_TEST)];
    scanner_create(scanner, N_SCANNER_POSITIONS_CONSTRUCTOR_TEST, pos);

    assert(N_SCANNER_POSITIONS_CONSTRUCTOR_TEST == get_num_scanners(scanner));
   
    float* scanner_pos = get_scanner_positions(scanner);
    for (int i = 0; i < N_SCANNER_POSITIONS_CONSTRUCTOR_TEST; i++)
    {
        assert(scanner_pos[i] == pos[i]);
    }

 
}


#define STATIC_POLY 1
#define STATIC_N_AST 1
#define TOLERANCE 1
#define N_SCANNER_POSITIONS_STATIC_TEST 5
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
    int vals[N_SCANNER_POSITIONS_STATIC_TEST] = {141, 111, 100, 111, 141};
    for (int i = 0; i < 5; i++)
    {
        assert(FLOAT_CMP(dist[i], vals[i], TOLERANCE));
    }
    return;
}
