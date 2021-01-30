import './App.css';
import React from 'react';
import MicRecorder from 'mic-recorder-to-mp3';
import { Button, Box, Card, CardContent, Container, List, ListItem, ListItemText, TextField, IconButton } from '@material-ui/core';
import { Delete, Sync, Mic, Stop } from '@material-ui/icons'
import BlockUI from 'react-block-ui';

class App extends React.Component {
  recorder = new MicRecorder({ bitRate: 128 });

  state = {
    memos: [],
    newMemoName: '',
    blocking: false
  }

  handleStart = () => {
    this.recorder
      .start()
      .then(() => {
        this.setState({ isRecording: true, hasRecording: false })
      })
  }

  handleStop = () => {
    this.recorder
      .stop()
      .getMp3()
      .then(([buffer, blob]) => {
        const blobUrl = URL.createObjectURL(blob)
        this.setState({ blobUrl, isRecording: false, hasRecording: true, blob })
      })
  }

  handleSave = () => {
    const data = new FormData();
    data.append('file', this.state.blob, 'recording.mp3')
    data.append('name', this.state.newMemoName)

    const requestOptions = {
      method: 'POST',
      body: data
    }

    this.toggleBlocking();

    fetch('/memos', requestOptions)
      .then(this.reset)
      .then(this.fetchMemos)
      .then(this.toggleBlocking)
  }

  handleNameChange = (event) => {
    this.setState({ newMemoName: event.target.value })
  }

  handleRefresh = () => {
    this.fetchMemos();
  }

  handleDelete = (id) => {
    fetch(`memos\\${id}`, { method: 'DELETE' })
      .then(this.fetchMemos)
  }

  toggleBlocking = () => {
    this.setState({ blocking: !this.state.blocking });
  }

  reset = () => {
    this.setState({
      isRecording: false,
      hasRecording: false,
      blobUrl: '',
      blob: null,
      newMemoName: `New Memo ${new Date().toLocaleString()}`
    })
  }

  fetchMemos = () => {
    return fetch('/memos')
      .then(res => res.json())
      .then(data => {
        this.setState({ memos: data })
      })
  }

  componentDidMount = () => {
    this.reset();
    this.fetchMemos();
    setInterval(() => this.fetchMemos(), 10000);
  }

  render() {
    return (
      <BlockUI blocking={this.state.blocking}>
        <Container maxWidth="sm">
          <Card>
            <CardContent>
              <Box display="flex" flexDirection="column">
                <TextField required value={this.state.newMemoName} onChange={this.handleNameChange} />
                <Box display="flex" justifyContent="space-evenly" margin="10px">
                  <IconButton onClick={this.handleStart} disabled={this.state.isRecording}>
                    <Mic />
                  </IconButton>
                  <IconButton onClick={this.handleStop} disabled={!this.state.isRecording}>
                    <Stop />
                  </IconButton>
                  <Button variant="contained" color="primary" onClick={this.handleSave} disabled={!this.state.hasRecording}>Save</Button>
                </Box>
                {this.state.hasRecording ? <audio src={this.state.blobUrl} controls="controls" width="100px" /> : null}
              </Box>
            </CardContent>
          </Card>
        </Container>
        <Container>
          <IconButton onClick={this.handleRefresh}>
            <Sync />
          </IconButton>
          <List>
            {
              this.state.memos.map((memo) => {
                return (
                  <ListItem key={memo.id}>
                    <IconButton onClick={() => this.handleDelete(memo.id)}>
                      <Delete />
                    </IconButton>
                    <ListItemText primary={memo.name} secondary={memo.transcription ?? 'Transcribing...'}></ListItemText>
                  </ListItem>
                )
              })
            }
          </List>
        </Container>
      </BlockUI>
    )
  }
}

export default App
