import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import TimeRangeSlider from '../components/TimeRangeSlider'

describe('TimeRangeSlider', () => {
  it('zeigt Start- und Endjahr', () => {
    render(<TimeRangeSlider value={[1960, 2024]} onChange={() => {}} />)
    expect(screen.getByText('1960')).toBeInTheDocument()
    expect(screen.getByText('2024')).toBeInTheDocument()
  })

  it('zeigt Label "Zeitraum"', () => {
    render(<TimeRangeSlider value={[1960, 2024]} onChange={() => {}} />)
    expect(screen.getByText('Zeitraum')).toBeInTheDocument()
  })

  it('rendert zwei Range-Inputs', () => {
    render(<TimeRangeSlider value={[1960, 2024]} onChange={() => {}} />)
    const inputs = screen.getAllByRole('slider')
    expect(inputs).toHaveLength(2)
  })

  it('ruft onChange mit neuen Werten auf (Startjahr)', () => {
    const onChange = vi.fn()
    render(<TimeRangeSlider value={[1960, 2024]} onChange={onChange} />)
    const [fromInput] = screen.getAllByRole('slider')
    fireEvent.change(fromInput, { target: { value: '1980' } })
    expect(onChange).toHaveBeenCalledWith([1980, 2024])
  })

  it('ruft onChange mit neuen Werten auf (Endjahr)', () => {
    const onChange = vi.fn()
    render(<TimeRangeSlider value={[1960, 2024]} onChange={onChange} />)
    const [, toInput] = screen.getAllByRole('slider')
    fireEvent.change(toInput, { target: { value: '2020' } })
    expect(onChange).toHaveBeenCalledWith([1960, 2020])
  })

  it('verhindert fromYear >= toYear', () => {
    const onChange = vi.fn()
    render(<TimeRangeSlider value={[2020, 2024]} onChange={onChange} />)
    const [fromInput] = screen.getAllByRole('slider')
    fireEvent.change(fromInput, { target: { value: '2025' } })
    // fromYear wird auf toYear-1 begrenzt
    expect(onChange).toHaveBeenCalledWith([2023, 2024])
  })

  it('zeigt Tick-Markierungen', () => {
    render(<TimeRangeSlider value={[1960, 2024]} onChange={() => {}} />)
    expect(screen.getByText('1880')).toBeInTheDocument()
    expect(screen.getByText('1950')).toBeInTheDocument()
  })
})
