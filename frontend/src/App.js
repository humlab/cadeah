import React from 'react';
import PropTypes from 'prop-types';
import Dropzone from 'react-dropzone-uploader';
import axios from 'axios';

import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.min.css';

import openSocket from 'socket.io-client';

import 'bootstrap/dist/css/bootstrap.min.css';
import 'react-dropzone-uploader/dist/styles.css';

const FileTable = ({ files }) => (
  <div className="files">
    <table className="table">
      <thead>
        <tr>
          <th scope="col">Name</th>
          <th scope="col">State</th>
        </tr>
      </thead>
      <tbody>
        {Object.keys(files).map((file, i) => (
          <FileListing key={i} filename={file} state={files[file]} />
        ))}
      </tbody>
    </table>
  </div>
);

FileTable.propTypes = {
  files: PropTypes.object.isRequired
};

const FileListing = ({ filename, state }) => (
  <tr>
    <th scope="row">{filename}</th>
    <td>{state}</td>
  </tr>
);

FileListing.propTypes = {
  filename: PropTypes.string.isRequired,
  state: PropTypes.string.isRequired
};

const socket = openSocket(`${process.env.REACT_APP_API_URL}`);

class App extends React.Component {
  state = {
    files: {}
  };

  componentDidMount() {
    this.listFiles();
    socket.on('state_change', this.updateFileState);
  }

  componentWillUnmount() {
    socket.off('state_change');
  }

  listFiles = async () => {
    // Fetch a list of file names, such as
    //
    // ["Megamind.avi", "caterpillar.webm", ...]
    const { data } = await axios.get(
      `${process.env.REACT_APP_API_URL}/files/list`
    );

    // Converted into,
    //
    // [{"Megamind.avi": "PROCESSED"}, {"caterpillar.webm": "PROCESSED"}]
    const processedFilesList = data.map(name => ({
      [name]: 'PROCESSED'
    }));

    // And then transformed to be
    //
    // {
    //   "Megamind.avi": "PROCESSED",
    //   "caterpillar.webm": "PROCESSED"
    // };
    const processedFilesObject = processedFilesList.reduce((map, x) => {
      Object.keys(x).forEach(key => {
        map[key] = x[key];
      });

      return map;
    }, {});

    // And overlayed with the previous state. { ...o1, ...o2 }
    // will overwrite the values in o1 with the values in o2
    // if there are overlapping keys
    this.setState(prevState => ({
      files: {
        ...prevState.files,
        ...processedFilesObject
      }
    }));
  };

  updateFileState = response => {
    this.setState(prevState => ({
      files: {
        ...prevState.files,
        [response.name]: response.state
      }
    }));
  };

  getUploadParams = () => {
    return { url: `${process.env.REACT_APP_API_URL}/files/upload` };
  };

  handleChangeStatus = ({ meta, remove }, status) => {
    if (status === 'headers_received') {
      toast.success(`${meta.name} uploaded!`);

      // Mark the file as unprocessed
      this.setState(prevState => ({
        files: {
          ...prevState.files,
          [meta.name]: 'UNPROCESSED'
        }
      }));

      // Remove the toast notification
      remove();
    } else if (status === 'aborted') {
      toast.error(`${meta.name}, upload failed...`);
    }
  };

  render() {
    return (
      <div className="app container">
        <div className="row">
          <div className="col">
            <Dropzone
              getUploadParams={this.getUploadParams}
              onChangeStatus={this.handleChangeStatus}
              styles={{
                dropzoneActive: { borderColor: 'green' }
              }}
            />
            <ToastContainer />
          </div>
        </div>
        <div className="row mt-5">
          <div className="col">
            <FileTable files={this.state.files} />
          </div>
        </div>
      </div>
    );
  }
}

export default App;