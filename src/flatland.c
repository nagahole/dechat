#include "flatland.h"

void flatland_protect(void* cluster, void* scanner)
{
    // Cluster not clear and no impact
    while ( !asteroid_cluster_clear(cluster) 
         && !asteroid_cluster_impact(cluster))
    {
   // TODO

    }
    return;
}
