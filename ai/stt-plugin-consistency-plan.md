# STT Plugin Consistency Plan

This document outlines a step-by-step plan to make the Moonshine and Deepgram STT plugin implementations more consistent, maintainable, and aligned with best practices.

## Overview

The current STT plugins have significant architectural and implementation inconsistencies that make them harder to maintain and potentially cause different behaviors under similar conditions. This plan addresses these issues systematically.

## Step 1: Standardize Base STT Class Contract

**Objective**: Establish a clear, consistent contract for all STT implementations to follow.

**Changes to Apply**:
1. **Update `getstream/plugins/stt/__init__.py`**:
   - Remove unused `_buffer` and `_buffer_lock` attributes from base STT class
   - Clarify the `_process_audio_impl` return type contract in docstring
   - Add standard error handling patterns to base class documentation
   - Define standard event emission patterns

2. **Create shared utilities**:
   - Add `_emit_transcript_event()` helper method to base class for consistent event emission
   - Add `_emit_error_event()` helper method to base class
   - Add `_validate_pcm_data()` helper method for input validation

**Expected Outcome**: Clear contract that both plugins can follow consistently.

---

## Step 2: Extract Common Audio Processing Utilities

**Objective**: Eliminate code duplication in audio format conversion and validation.

**Changes to Apply**:
1. **Create `getstream/audio/pcm_utils.py`**:
   ```python
   def pcm_to_numpy_array(pcm_data: PcmData) -> np.ndarray
   def numpy_array_to_bytes(audio_array: np.ndarray) -> bytes
   def validate_sample_rate_compatibility(input_rate: int, target_rate: int, plugin_name: str) -> None
   def log_audio_processing_info(pcm_data: PcmData, target_rate: int, plugin_name: str) -> None
   ```

2. **Update both plugins** to use these shared utilities instead of duplicated code

**Expected Outcome**: No more duplicated audio conversion logic between plugins.

---

## Step 3: Standardize Configuration and Initialization

**Objective**: Make plugin initialization patterns consistent and predictable.

**Changes to Apply**:
1. **Moonshine plugin**:
   - Add validation for all initialization parameters
   - Add environment variable support for model selection (e.g., `MOONSHINE_MODEL`)
   - Standardize parameter naming conventions

2. **Deepgram plugin**:
   - Add model name validation similar to Moonshine
   - Improve parameter validation and error messages
   - Ensure consistent parameter naming

3. **Both plugins**:
   - Use consistent default values where appropriate
   - Add comprehensive parameter validation with clear error messages
   - Document all initialization parameters consistently

**Expected Outcome**: Both plugins have similar initialization patterns and validation.

---

## Step 4: Unify Event Handling Architecture

**Objective**: Make both plugins use the same event emission pattern for consistency.

**Changes to Apply**:
1. **Decide on architecture**: Use the base class pattern (Moonshine's approach) as the standard
   - Simpler and more predictable
   - Better aligned with base class design
   - Easier to test and debug

2. **Update Deepgram plugin**:
   - Remove `BackgroundDispatcher` class
   - Modify `_process_audio_impl` to return `List[Tuple[bool, str, Dict[str, Any]]]`
   - Let base class handle event emission
   - Simplify connection event handlers to collect results instead of emitting directly

3. **Update base class** (if needed):
   - Ensure robust handling of the return pattern
   - Add proper error handling for malformed returns

**Expected Outcome**: Both plugins use the same event emission pattern through the base class.

---

## Step 5: Standardize Error Handling and Resilience

**Objective**: Implement consistent error handling and recovery patterns.

**Changes to Apply**:
1. **Create shared error handling utilities**:
   - Add `getstream/plugins/stt/error_handling.py` with common patterns
   - Define standard retry mechanisms
   - Create consistent error logging patterns

2. **Update both plugins**:
   - Use consistent exception handling patterns
   - Implement similar retry logic where appropriate
   - Use standardized error messages and logging

3. **Add resilience patterns**:
   - Connection retry logic for Deepgram
   - Model loading retry logic for Moonshine
   - Graceful degradation patterns

**Expected Outcome**: Both plugins handle errors consistently and have similar resilience characteristics.

---

## Step 6: Unify Logging Patterns

**Objective**: Make logging consistent across both plugins for better debugging and monitoring.

**Changes to Apply**:
1. **Create logging standards**:
   - Define when to use DEBUG vs INFO vs WARNING vs ERROR
   - Standardize structured logging patterns using `extra={}`
   - Create consistent log message formats

2. **Update both plugins**:
   - Align log levels for similar operations
   - Use consistent structured logging with standard field names
   - Add missing debug information where needed

3. **Create shared logging utilities**:
   - Add helper functions for common logging patterns
   - Ensure consistent timing and performance logging

**Expected Outcome**: Consistent logging patterns that make debugging easier across both plugins.

---

## Step 7: Standardize Test Infrastructure

**Objective**: Make test patterns consistent and reduce test code duplication.

**Changes to Apply**:
1. **Create shared test utilities**:
   - Add `getstream/plugins/stt/test_utils.py` with common test patterns
   - Create standard mock factories for STT testing
   - Add shared audio data fixtures

2. **Update test fixtures**:
   - Standardize fixture naming (`audio_data_16k`, `audio_data_48k`, etc.)
   - Create consistent mock strategies
   - Share audio generation logic

3. **Align test coverage**:
   - Ensure both plugins test similar scenarios
   - Add missing test cases to achieve parity
   - Use consistent assertion patterns

**Expected Outcome**: Test suites that are easier to maintain and provide consistent coverage.

---

## Step 8: Improve Documentation Consistency

**Objective**: Ensure both plugins have consistent, comprehensive documentation.

**Changes to Apply**:
1. **Standardize docstrings**:
   - Use consistent format for class and method documentation
   - Document all parameters, return values, and exceptions
   - Add usage examples where helpful

2. **Update README files**:
   - Use consistent structure and formatting
   - Include similar sections (installation, usage, configuration, etc.)
   - Add troubleshooting sections

3. **Add inline comments**:
   - Explain complex operations consistently
   - Document design decisions and trade-offs
   - Add performance considerations where relevant

**Expected Outcome**: Both plugins have comprehensive, consistent documentation.

---

## Step 9: Align Dependency Management

**Objective**: Make dependency management patterns consistent and maintainable.

**Changes to Apply**:
1. **Review dependency strategies**:
   - Evaluate Moonshine's git dependency approach
   - Consider moving to PyPI packages where possible
   - Ensure version pinning strategies are consistent

2. **Update pyproject.toml files**:
   - Use consistent version constraints
   - Align optional dependencies
   - Ensure workspace configuration is identical

3. **Add dependency validation**:
   - Add runtime checks for required dependencies
   - Provide clear error messages for missing dependencies
   - Document dependency installation clearly

**Expected Outcome**: Consistent dependency management that's easy to maintain and troubleshoot.

---

## Step 10: Performance and Monitoring Alignment

**Objective**: Ensure both plugins have consistent performance characteristics and monitoring.

**Changes to Apply**:
1. **Add performance monitoring**:
   - Consistent timing measurements
   - Memory usage tracking where appropriate
   - Throughput monitoring for real-time scenarios

2. **Optimize similar operations**:
   - Ensure audio processing efficiency is comparable
   - Align memory management patterns
   - Use consistent caching strategies where applicable

3. **Add performance tests**:
   - Benchmark both plugins under similar conditions
   - Test memory usage patterns
   - Validate real-time performance characteristics

**Expected Outcome**: Both plugins have similar performance characteristics and monitoring capabilities.

---

## Implementation Guidelines

### Order of Implementation
1. **Steps 1-3**: Foundation work (base class, utilities, configuration)
2. **Steps 4-6**: Core functionality alignment (events, errors, logging)
3. **Steps 7-8**: Quality and maintainability (tests, documentation)
4. **Steps 9-10**: Operational concerns (dependencies, performance)

### Testing Strategy
- Run full test suite after each step
- Add integration tests to verify consistency
- Test both plugins under similar conditions
- Validate that existing functionality is preserved

### Rollback Plan
- Each step should be implementable as a separate commit
- Maintain backward compatibility where possible
- Document any breaking changes clearly
- Provide migration guides for users if needed

### Success Criteria
- [ ] Both plugins pass identical test scenarios
- [ ] Code duplication is eliminated
- [ ] Event handling is consistent
- [ ] Error handling patterns are aligned
- [ ] Documentation is comprehensive and consistent
- [ ] Performance characteristics are comparable
- [ ] Maintenance burden is reduced

## Post-Implementation Benefits

1. **Easier Maintenance**: Consistent patterns make it easier to maintain both plugins
2. **Better Testing**: Shared utilities and patterns improve test coverage
3. **Reduced Bugs**: Consistent error handling reduces edge case bugs
4. **Better User Experience**: Consistent behavior across different STT providers
5. **Easier Onboarding**: New contributors can understand patterns more easily
6. **Future Plugin Development**: Clear patterns for implementing new STT plugins
