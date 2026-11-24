import { fetchApi } from '../../../app/config/api';
import { BlockchainConfig } from '../../../types/credential';

export async function getBlockchainConfig(): Promise<BlockchainConfig> {
  return fetchApi<BlockchainConfig>('/blockchain/config');
}
