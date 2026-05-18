interface FinancialYearLike {
  code?: string;
  name?: string;
  startDate?: string;
  endDate?: string;
}

function formatFinancialYearRange(startYear: number, endYear: number) {
  return `${startYear}-${String(endYear).slice(-2)}`;
}

function extractFinancialYearRange(value?: string) {
  if (!value) {
    return null;
  }

  const match = value.match(/(\d{4})\s*-\s*(\d{2,4})/);
  if (!match) {
    return null;
  }

  const startYear = Number(match[1]);
  const endYear = match[2].length === 2 ? Number(`${String(startYear).slice(0, 2)}${match[2]}`) : Number(match[2]);
  if (Number.isNaN(startYear) || Number.isNaN(endYear)) {
    return null;
  }

  return formatFinancialYearRange(startYear, endYear);
}

export function getFinancialYearValue(financialYear: FinancialYearLike) {
  if (financialYear.startDate) {
    const startYear = new Date(financialYear.startDate).getUTCFullYear();
    const endYear = financialYear.endDate
      ? new Date(financialYear.endDate).getUTCFullYear()
      : startYear + 1;
    if (!Number.isNaN(startYear) && !Number.isNaN(endYear)) {
      return formatFinancialYearRange(startYear, endYear);
    }
  }

  return (
    extractFinancialYearRange(financialYear.code) ??
    extractFinancialYearRange(financialYear.name) ??
    financialYear.code ??
    financialYear.name ??
    ''
  );
}
