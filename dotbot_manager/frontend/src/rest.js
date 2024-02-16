import axios from 'axios';

export const apiFetchACL = async () => {
  return await axios.get(
    // `${process.env.REACT_APP_DOTBOTS_BASE_URL}/controller/dotbots`,
    `http://127.0.0.1:8000/manager/acl`,
  ).then(res => res.data);
}
