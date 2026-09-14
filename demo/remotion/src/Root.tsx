import React from 'react'
import { Composition } from 'remotion'
import { FPS, RESQIO_DURATION, Resqio } from './Resqio'

export const RemotionRoot: React.FC = () => (
  <Composition id="Resqio" component={Resqio} durationInFrames={RESQIO_DURATION} fps={FPS} width={1920} height={1080} />
)
