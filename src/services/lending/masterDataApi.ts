import api from '@/services/api';

export type MasterDataType = 'text' | 'number' | 'boolean' | 'date';

export interface MasterFieldDescriptor {
  key: string;
  label: string;
  dataType: MasterDataType;
  required: boolean;
  editable: boolean;
  system: boolean;
}

export interface MasterCatalogItem {
  key: string;
  label: string;
  description: string;
  group: string;
  sourceTable: string;
  sourceOfTruth: string;
  consumerScreens: string[];
  seedSource: string;
  fields: MasterFieldDescriptor[];
}

export interface MasterCatalogResponse {
  items: MasterCatalogItem[];
}

export interface MasterRow {
  id: string;
  data: Record<string, unknown>;
}

export interface MasterRowListResponse {
  key: string;
  items: MasterRow[];
  total: number;
  page: number;
  pageSize: number;
}

export interface MasterRowMutation {
  data: Record<string, unknown>;
}

function idempotencyHeaders(): { 'Idempotency-Key': string } {
  return { 'Idempotency-Key': crypto.randomUUID() };
}

export const lendingMasterDataApi = {
  async getCatalog(): Promise<MasterCatalogResponse> {
    const { data } = await api.get<MasterCatalogResponse>('/lending/masters/catalog');
    return data;
  },

  async listRows(
    masterKey: string,
    params?: { page?: number; pageSize?: number; optionGroup?: string },
  ): Promise<MasterRowListResponse> {
    const { data } = await api.get<MasterRowListResponse>(`/lending/masters/${masterKey}/rows`, {
      params,
    });
    return data;
  },

  async createRow(masterKey: string, payload: MasterRowMutation): Promise<MasterRow> {
    const { data } = await api.post<MasterRow>(`/lending/masters/${masterKey}/rows`, payload, {
      headers: idempotencyHeaders(),
    });
    return data;
  },

  async updateRow(
    masterKey: string,
    rowId: string,
    payload: MasterRowMutation,
  ): Promise<MasterRow> {
    const { data } = await api.put<MasterRow>(
      `/lending/masters/${masterKey}/rows/${rowId}`,
      payload,
      { headers: idempotencyHeaders() },
    );
    return data;
  },

  async deleteRow(masterKey: string, rowId: string): Promise<void> {
    await api.delete(`/lending/masters/${masterKey}/rows/${rowId}`, {
      headers: idempotencyHeaders(),
    });
  },
};
