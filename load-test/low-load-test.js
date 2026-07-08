import http from 'k6/http';
import { sleep } from 'k6';

export const options = {
  stages: [
    { duration: '20s', target: 15 },
    { duration: '40s', target: 15 },
    { duration: '20s', target: 0 },
  ],
};

const BASE_URL = 'http://a8ec4099aaa854dbdba109fda0ab4fb3-1852957901.ap-northeast-2.elb.amazonaws.com';

export default function () {
  http.get(`${BASE_URL}/hospitals/`);
  sleep(0.1);
}