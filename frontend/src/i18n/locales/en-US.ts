/**
 * English dictionary
 *
 * Covers App.vue (nav + switch button) + Home.vue (all text)
 * Extend in D3 when new pages are written
 */
export default {
  app: {
    name: 'EVOLUTION AI',
    version: 'v0.3.0',
    nav: {
      home: 'Home',
      designer: 'Designer',
      quality: 'Quality',
      optimize: 'AI Optimize',
      storyboard: 'Storyboard',
      projects: 'Projects',
    },
    lang: {
      zh: '中文',
      en: 'English',
      switchTip: 'Switch language',
    },
  },
  home: {
    hero: {
      title: 'EVOLUTION AI',
      subtitle: 'Parametric + AI-driven automotive styling platform',
    },
    status: {
      backendOnline: 'Backend: online',
      backendOffline: 'Backend: offline',
      backendUnknown: 'Backend: unknown',
      apiEndpoints: 'API v{version} · {count} endpoints',
      m3Skeleton: 'M3 W1-D{day} skeleton',
    },
    sectionTitle: '{count} Business Modules',
    modules: {
      designer: {
        label: 'Designer',
        desc: '22-dim params + real-time 3D preview',
      },
      quality: {
        label: 'Quality',
        desc: 'G0/G1/G2 + reflection analysis',
      },
      optimize: {
        label: 'AI Optimize',
        desc: 'WebSocket real-time progress (M2.5)',
      },
      storyboard: {
        label: 'Storyboard',
        desc: 'AI video script + rendering',
      },
      projects: {
        label: 'Projects',
        desc: 'CRUD + history tasks',
      },
    },
  },
  common: {
    loading: 'Loading…',
    error: 'Error',
    retry: 'Retry',
    confirm: 'Confirm',
    cancel: 'Cancel',
    save: 'Save',
    delete: 'Delete',
    edit: 'Edit',
    create: 'Create',
    search: 'Search',
  },
  error: {
    network: 'Network error, please check your connection',
    timeout: 'Request timeout, please retry',
    server4xx: 'Request error ({code})',
    server5xx: 'Server error ({code})',
    unknown: 'Unknown error',
  },
  // ===== W1-D3 business pages =====
  designer: {
    title: 'Designer',
    subtitle: '22-dim parameters + real-time 3D preview',
    params: {
      bodyLength: 'Body Length (L)',
      bodyWidth: 'Body Width (W)',
      bodyHeight: 'Body Height (H)',
      wheelbase: 'Wheelbase',
      frontOverhang: 'Front Overhang',
      rearOverhang: 'Rear Overhang',
      groundClearance: 'Ground Clearance',
      roofHeight: 'Roof Height',
      windshieldAngle: 'Windshield Angle',
      rearWindowAngle: 'Rear Window Angle',
      hoodAngle: 'Hood Angle',
    },
    actions: {
      generate: 'Generate 3D Model',
      reset: 'Reset Params',
      save: 'Save Project',
    },
    status: {
      ready: 'Ready',
      generating: 'Generating...',
      done: 'Done',
    },
  },
  quality: {
    title: 'Quality',
    subtitle: 'G0/G1/G2 continuity + reflection analysis',
    metrics: {
      g0Count: 'G0 Edges',
      g1Count: 'G1 Edges',
      g2Count: 'G2 Edges',
      g2Ratio: 'G2 Ratio',
      reflection: 'Reflection Score',
      meanCurvature: 'Mean Curvature',
      maxJump: 'Max Normal Jump',
    },
    grade: {
      A: 'Class A Surface',
      B: 'Class B Surface',
      C: 'Class C Surface',
      D: 'Class D Surface',
    },
    actions: {
      assess: 'Start Assessment',
      preset: 'Preset Surface',
    },
  },
  optimize: {
    title: 'AI Optimize',
    subtitle: 'WebSocket live progress · Simulated Annealing',
    shape: {
      sphere: 'Sphere',
      plane: 'Plane with Noise',
      cylinder: 'Cylinder',
      carBody: 'Car Body Side',
    },
    params: {
      shape: 'Select Surface',
      maxIter: 'Max Iterations',
      panelName: 'Panel Name',
      seed: 'Random Seed',
    },
    actions: {
      start: 'Start Async Optimize',
      startSync: 'Run Sync',
      cancel: 'Cancel Task',
    },
    progress: {
      title: 'Live Progress',
      currentIter: 'Current Iter',
      bestScore: 'Best Score',
      elapsed: 'Elapsed',
    },
    history: {
      title: 'Task History',
      empty: 'No task history',
      view: 'View Detail',
    },
  },
  optimizeDetail: {
    title: 'Optimize Task Detail',
    taskInfo: 'Task Info',
    convergence: 'Convergence Curve',
    result: 'Result',
    initial: 'Initial',
    final: 'Final',
    improvement: 'Improvement',
  },
  storyboard: {
    title: 'Storyboard',
    subtitle: 'AI video script + render',
    params: {
      productName: 'Product Name',
      duration: 'Duration (sec)',
      style: 'Visual Style',
      template: 'Script Template',
    },
    templates: {
      carPromotion: 'Car Promotion',
      techDemo: 'Tech Demo',
      minimalShowcase: 'Minimal Showcase',
    },
    actions: {
      generate: 'Generate Storyboard',
      render: 'Render',
    },
    scenes: {
      title: 'Scenes',
      empty: 'No scenes',
    },
  },
  storyboardDetail: {
    title: 'Storyboard Project Detail',
    scenes: 'Scenes',
    render: 'Render Output',
    export: 'Export',
  },
  projects: {
    title: 'Projects',
    subtitle: 'CRUD + task history',
    actions: {
      create: 'New Project',
      search: 'Search',
      refresh: 'Refresh',
    },
    table: {
      id: 'ID',
      name: 'Project Name',
      surfaceType: 'Surface Type',
      status: 'Status',
      createdAt: 'Created At',
      updatedAt: 'Updated At',
      actions: 'Actions',
    },
    status: {
      draft: 'Draft',
      running: 'Running',
      success: 'Success',
      failed: 'Failed',
    },
    empty: 'No projects',
  },
  projectDetail: {
    title: 'Project Detail',
    tabs: {
      overview: 'Overview',
      model3d: '3D Model',
      optimize: 'Optimize History',
      quality: 'Quality',
      storyboard: 'Storyboard',
    },
    actions: {
      back: 'Back to List',
      delete: 'Delete',
    },
  },
  errors: {
    notFound: {
      title: '404 · Page Lost',
      desc: "The page you want is not in the world, go back and rest?",
      back: 'Back Home',
    },
    serverError: {
      title: '500 · Server Down',
      desc: 'Backend process was recycled / crashed by sandbox, retry in 5s or go home',
      retry: 'Retry',
      back: 'Back Home',
    },
  },
} as const