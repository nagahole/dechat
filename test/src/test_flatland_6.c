#include "test_flatland.h"

int main()
{
    flatland_swarm();
    return 0;
}

#define POLY_SIZE_Y 2
#define POLY_SIZE_X 2
#define N_AST 6
#define TOLERANCE 1
#define N_SCANNER_POSITIONS 5
void flatland_swarm()
{
    // Create cluster object
    char cluster[SIZEOF_ASTEROID_CLUSTER(N_AST)];
    asteroid_cluster_create(cluster, N_AST, TOLERANCE); 

    // Create Polynomials
    char poly_x[SIZEOF_POLYNOMIAL(POLY_SIZE_X) * N_AST];
    char poly_y[SIZEOF_POLYNOMIAL(POLY_SIZE_Y) * N_AST];

    for (int i = 0; i < N_AST; i++)
    {
        float poly_vals_x[POLY_SIZE_X] = {2 * i, 0};
        float poly_vals_y[POLY_SIZE_Y] = {-20, 1001 + i * 100}; 
        
        char* curr_poly_x = poly_x + (i * SIZEOF_POLYNOMIAL(POLY_SIZE_X));
        char* curr_poly_y = poly_y + (i * SIZEOF_POLYNOMIAL(POLY_SIZE_Y));

        polynomial_create(
                curr_poly_x,
                POLY_SIZE_X, 
                poly_vals_x);
        polynomial_create(
                curr_poly_y,
                POLY_SIZE_Y, 
                poly_vals_y);

        // Add asteroid to cluster
        asteroid_cluster_add_asteroid(cluster, curr_poly_x, curr_poly_y); 
    }

    // Create the scanner
    char scanner[SIZEOF_SCANNER(N_SCANNER_POSITIONS)];
    float scanner_pos[N_SCANNER_POSITIONS] = {0, 100, 200, 300, 400}; 
    scanner_create(scanner, N_SCANNER_POSITIONS, scanner_pos); 

    assert(0 == asteroid_cluster_clear(cluster));
    
    flatland_protect(cluster, scanner);
    
    assert(0 == asteroid_cluster_impact(cluster)); 
    assert(1 == asteroid_cluster_clear(cluster));

    return;
}
