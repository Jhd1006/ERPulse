import http from 'k6/http';
import { sleep } from 'k6';

export const options = {
  stages: [
    { duration: '20s', target: 15 },
    { duration: '40s', target: 15 },
    { duration: '20s', target: 0 },
  ],
};

// ELB 주소 확인: kubectl get svc erpulse-api -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
const BASE_URL = 'CHANGE_ME';

export default function () {
  http.get(`${BASE_URL}/hospitals/`);
  sleep(0.1);
}
