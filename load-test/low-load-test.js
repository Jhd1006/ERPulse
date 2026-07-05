import http from 'k6/http';
import { sleep } from 'k6';

export const options = {
  stages: [
    { duration: '20s', target: 15 },
    { duration: '40s', target: 15 },
    { duration: '20s', target: 0 },
  ],
};

const BASE_URL = 'http://aa7e9695d841b4764ae84b33e4613913-606579759.ap-northeast-2.elb.amazonaws.com';

export default function () {
  http.get(`${BASE_URL}/hospitals/`);
  sleep(0.1);
}