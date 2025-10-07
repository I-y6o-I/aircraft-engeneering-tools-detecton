declare module 'vue-konva' {
  import { ComponentPublicInstance } from 'vue'
  import Konva from 'konva'
  
  export const VueKonva: any
  
  export interface KonvaNode {
    getNode(): Konva.Node
  }

  export interface StageConfig {
    width: number
    height: number
    scaleX?: number
    scaleY?: number
    x?: number
    y?: number
  }

  export interface ImageConfig {
    x?: number
    y?: number
    width?: number
    height?: number
    image?: HTMLImageElement
  }

  export interface RectConfig {
    x?: number
    y?: number
    width?: number
    height?: number
    fill?: string
    stroke?: string
    strokeWidth?: number
    listening?: boolean
    name?: string
    dash?: number[]
  }

  export interface TextConfig {
    x?: number
    y?: number
    text?: string
    fontSize?: number
    fontFamily?: string
    fill?: string
    align?: string
    listening?: boolean
    shadowColor?: string
    shadowBlur?: number
    shadowOffsetX?: number
    shadowOffsetY?: number
  }

  export interface CircleConfig {
    x?: number
    y?: number
    radius?: number
    fill?: string
    stroke?: string
    strokeWidth?: number
    draggable?: boolean
  }
}
