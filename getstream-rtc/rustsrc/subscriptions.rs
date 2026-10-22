use std::collections::HashMap;

use pyo3::prelude::*;

use crate::participants::TrackType;
use crate::repr::repr;

/// The subscription rule for the participants of one role, or the default rule.
#[pyclass(frozen, module = "getstream_rtc", from_py_object)]
#[derive(Clone)]
pub struct TrackSubscriptionConfig {
    #[pyo3(get)]
    track_types: Vec<TrackType>,
    /// `(width, height)` requested for `VIDEO` tracks.
    #[pyo3(get)]
    video_dimension: (u32, u32),
    /// `(width, height)` requested for `SCREEN_SHARE` tracks.
    #[pyo3(get)]
    screenshare_dimension: (u32, u32),
}

#[pymethods]
impl TrackSubscriptionConfig {
    /// A `None` argument keeps the SDK default.
    #[new]
    #[pyo3(signature = (track_types=None, video_dimension=None, screenshare_dimension=None))]
    fn new(
        track_types: Option<Vec<TrackType>>,
        video_dimension: Option<(u32, u32)>,
        screenshare_dimension: Option<(u32, u32)>,
    ) -> Self {
        let default = Self::from(getstream::rtc::TrackSubscriptionConfig::default());
        Self {
            track_types: track_types.unwrap_or(default.track_types),
            video_dimension: video_dimension.unwrap_or(default.video_dimension),
            screenshare_dimension: screenshare_dimension.unwrap_or(default.screenshare_dimension),
        }
    }

    fn __repr__(&self, py: Python<'_>) -> PyResult<String> {
        Ok(format!(
            "TrackSubscriptionConfig(track_types={}, video_dimension={}, screenshare_dimension={})",
            repr(py, self.track_types.clone())?,
            repr(py, self.video_dimension)?,
            repr(py, self.screenshare_dimension)?
        ))
    }
}

impl From<getstream::rtc::TrackSubscriptionConfig> for TrackSubscriptionConfig {
    fn from(config: getstream::rtc::TrackSubscriptionConfig) -> Self {
        Self {
            track_types: config.track_types.into_iter().map(Into::into).collect(),
            video_dimension: config.video_dimension,
            screenshare_dimension: config.screenshare_dimension,
        }
    }
}

impl From<TrackSubscriptionConfig> for getstream::rtc::TrackSubscriptionConfig {
    fn from(config: TrackSubscriptionConfig) -> Self {
        Self {
            track_types: config.track_types.into_iter().map(Into::into).collect(),
            video_dimension: config.video_dimension,
            screenshare_dimension: config.screenshare_dimension,
        }
    }
}

/// Which remote tracks to receive. The SDK applies the rule of the first role
/// in `participant.roles` that has an entry in `role_filters`, or else
/// `default`, and keeps at most `max_subscriptions` tracks.
#[pyclass(frozen, module = "getstream_rtc", from_py_object)]
#[derive(Clone)]
pub struct SubscriptionConfig {
    #[pyo3(get)]
    default: TrackSubscriptionConfig,
    #[pyo3(get)]
    role_filters: HashMap<String, TrackSubscriptionConfig>,
    #[pyo3(get)]
    max_subscriptions: Option<usize>,
}

#[pymethods]
impl SubscriptionConfig {
    /// A `None` argument keeps the SDK default.
    #[new]
    #[pyo3(signature = (default=None, role_filters=None, max_subscriptions=None))]
    fn new(
        default: Option<TrackSubscriptionConfig>,
        role_filters: Option<HashMap<String, TrackSubscriptionConfig>>,
        max_subscriptions: Option<usize>,
    ) -> Self {
        Self {
            default: default
                .unwrap_or_else(|| getstream::rtc::TrackSubscriptionConfig::default().into()),
            role_filters: role_filters.unwrap_or_default(),
            max_subscriptions,
        }
    }

    fn __repr__(&self, py: Python<'_>) -> PyResult<String> {
        Ok(format!(
            "SubscriptionConfig(default={}, role_filters={}, max_subscriptions={})",
            repr(py, self.default.clone())?,
            repr(py, self.role_filters.clone())?,
            repr(py, self.max_subscriptions)?
        ))
    }
}

impl From<SubscriptionConfig> for getstream::rtc::SubscriptionConfig {
    fn from(config: SubscriptionConfig) -> Self {
        Self {
            default: config.default.into(),
            role_filters: config
                .role_filters
                .into_iter()
                .map(|(role, rule)| (role, rule.into()))
                .collect(),
            max_subscriptions: config.max_subscriptions,
        }
    }
}
