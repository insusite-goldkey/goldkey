const fallbackData = {
  customer: {
    name: '',
    job: '',
    birthYear: '',
    subscriptionDate: '',
  },
  coverage: {
    hoffmannGap: 0,
    silsonGeneration: null,
  },
  tasks: [],
  aiReport: null,
};

function isValidCustomer(customer) {
  return (
    customer !== null &&
    typeof customer === 'object' &&
    typeof customer.name === 'string'
  );
}

function isValidCoverage(coverage) {
  return (
    coverage !== null &&
    typeof coverage === 'object' &&
    typeof coverage.hoffmannGap === 'number'
  );
}

function isValidTasks(tasks) {
  return Array.isArray(tasks);
}

export function validateAndRecover(state) {
  let recovered = false;
  const result = { ...state };

  if (!isValidCustomer(state.customer)) {
    console.warn('[Watchdog] customer 상태 손상 → fallback 복구');
    result.customer = { ...fallbackData.customer };
    recovered = true;
  }

  if (!isValidCoverage(state.coverage)) {
    console.warn('[Watchdog] coverage 상태 손상 → fallback 복구');
    result.coverage = { ...fallbackData.coverage };
    recovered = true;
  }

  if (!isValidTasks(state.tasks)) {
    console.warn('[Watchdog] tasks 상태 손상 → fallback 복구');
    result.tasks = [];
    recovered = true;
  }

  if (recovered) {
    console.warn('[Watchdog] 상태 복구 완료. 영업 현장 중단 없이 진행합니다.');
  }

  return { state: result, recovered };
}

export function runWatchdog(getState, setState) {
  try {
    const current = getState();
    const { state: recovered, recovered: wasRecovered } = validateAndRecover(current);
    if (wasRecovered) {
      setState(recovered);
    }
    return wasRecovered;
  } catch (e) {
    console.error('[Watchdog] 치명적 오류, 전체 fallback 적용:', e);
    setState({ ...fallbackData });
    return true;
  }
}
