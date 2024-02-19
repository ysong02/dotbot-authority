import axios from 'axios';

export const apiFetchACL = async () => {
  return await axios.get(
    // `${process.env.REACT_APP_DOTBOTS_BASE_URL}/controller/dotbots`,
    `http://localhost:18000/api/v1/acl`,
  ).then(res => res.data);
}
