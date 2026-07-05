import http from 'k6/http';
import { sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 20 },
    { duration: '1m', target: 50 },
    { duration: '2m', target: 100 },
    { duration: '1m', target: 0 },
  ],
};

const BASE_URL = 'http://aa7e9695d841b4764ae84b33e4613913-606579759.ap-northeast-2.elb.amazonaws.com';

export default function () {
  http.get(`${BASE_URL}/cpu/stress`);
  sleep(0.1);
}