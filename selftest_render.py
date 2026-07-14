#!/usr/bin/env python3
"""
3D 渲染自测验证工具
用途：在修改 app.py 后，自动验证几何正确性和渲染可行性
无需 Streamlit，纯 headless 运行

使用方式：
  python selftest_render.py                  # 运行全部测试
  python selftest_render.py --part=hood      # 只测试单个零件
  python selftest_render.py --group=wheels   # 测试一组零件
  python selftest_render.py --export=obj     # 导出 OBJ 文件
  python selftest_render.py --render=png     # 渲染静态 PNG 图片
"""

import sys
import os
import argparse
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np

# Mock Streamlit to avoid GUI dependencies
class MockStreamlit:
    class session_state(dict):
        @staticmethod
        def get(k, d=None):
            return d
    class sidebar:
        @staticmethod
        def slider(*a, **kw):
            return a[2] if len(a) > 2 else kw.get('value', 0)
        @staticmethod
        def markdown(*a, **kw): pass
        @staticmethod
        def text(*a, **kw): pass
    @staticmethod
    def columns(n): return [MockContext() for _ in range(n)]
    @staticmethod
    def plotly_chart(*a, **kw): pass
    @staticmethod
    def expander(*a, **kw): return MockContext()
    @staticmethod
    def info(*a, **kw): pass
    @staticmethod
    def write(*a, **kw): pass
    @staticmethod
    def metric(*a, **kw): pass
    @staticmethod
    def success(*a, **kw): pass
    @staticmethod
    def error(*a, **kw): pass
    @staticmethod
    def warning(*a, **kw): pass

class MockContext:
    def __enter__(self): return self
    def __exit__(self, *a): pass
    def plotly_chart(self, *a, **kw): pass
    def markdown(self, *a, **kw): pass
    def write(self, *a, **kw): pass

sys.modules['streamlit'] = MockStreamlit

# Now import app.py functions
try:
    # Read and exec app.py (skip the main block)
    app_code = open(PROJECT_ROOT / 'app.py').read()
    if 'if __name__' in app_code:
        app_code = app_code.split('if __name__')[0]
    exec(app_code)
    APP_LOADED = True
except Exception as e:
    print(f"❌ Failed to load app.py: {e}")
    APP_LOADED = False


class RenderValidator:
    """3D 渲染自测验证器"""
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or (PROJECT_ROOT / 'selftest_output')
        self.output_dir.mkdir(exist_ok=True)
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'geometry_tests': [],
            'render_tests': [],
            'export_tests': [],
            'errors': [],
            'warnings': [],
        }
    
    def log(self, msg: str):
        print(msg)
    
    def add_error(self, test: str, msg: str):
        self.results['errors'].append({'test': test, 'message': msg})
        self.log(f"  ❌ {msg}")
    
    def add_warning(self, test: str, msg: str):
        self.results['warnings'].append({'test': test, 'message': msg})
        self.log(f"  ⚠️  {msg}")
    
    def add_pass(self, test: str, msg: str = ''):
        self.log(f"  ✅ {msg or test}")
    
    # ====== Geometry Validation ======
    
    def validate_geometry(self, part_name: str, part_data: dict) -> dict:
        """Validate a single part's geometry"""
        result = {'name': part_name, 'passed': True, 'checks': []}
        
        verts = part_data.get('vertices')
        faces = part_data.get('faces')
        
        if verts is None or faces is None:
            result['passed'] = False
            result['checks'].append(('vertices_faces', False, 'Missing vertices or faces'))
            return result
        
        # Check 1: Vertices are finite
        if not np.all(np.isfinite(verts)):
            result['passed'] = False
            result['checks'].append(('finite_verts', False, 'Vertices contain NaN or Inf'))
        
        # Check 2: Faces indices are valid
        max_idx = faces.max() if len(faces) > 0 else 0
        if max_idx >= len(verts):
            result['passed'] = False
            result['checks'].append(('valid_faces', False, f'Face index {max_idx} >= vertex count {len(verts)}'))
        
        # Check 3: Bounding box is reasonable
        bbox_min = verts.min(axis=0)
        bbox_max = verts.max(axis=0)
        bbox_size = bbox_max - bbox_min
        
        if np.any(bbox_size < 1e-6):
            result['passed'] = False
            result['checks'].append(('bbox_size', False, f'Degenerate bounding box: {bbox_size}'))
        
        if np.any(bbox_size > 10.0):  # Car parts shouldn't be > 10m in any dimension
            self.add_warning('geometry', f'{part_name}: Large bounding box {bbox_size}')
        
        # Check 4: Vertex count is reasonable
        if len(verts) < 3:
            result['passed'] = False
            result['checks'].append(('min_verts', False, f'Too few vertices: {len(verts)}'))
        
        if len(verts) > 100000:
            self.add_warning('geometry', f'{part_name}: Very high vertex count {len(verts)}')
        
        # Check 5: Face count is reasonable
        if len(faces) < 1:
            result['passed'] = False
            result['checks'].append(('min_faces', False, f'Too few faces: {len(faces)}'))
        
        # Record stats
        result['stats'] = {
            'vertex_count': len(verts),
            'face_count': len(faces),
            'bbox_min': bbox_min.tolist(),
            'bbox_max': bbox_max.tolist(),
            'bbox_size': bbox_size.tolist(),
        }
        
        return result
    
    def test_single_part(self, part_name: str, params=None):
        """Test a single part's geometry and rendering"""
        self.log(f"\n🔍 Testing part: {part_name}")
        
        if not APP_LOADED:
            self.add_error(part_name, 'app.py not loaded')
            return
        
        try:
            if params is None:
                # Create params directly from CAR_TYPE_PRESETS
                preset = CAR_TYPE_PRESETS['sedan']
                params = CoreCarParams(
                    length=preset['length'] / 1000.0,
                    width=preset['width'] / 1000.0,
                    height=preset['height'] / 1000.0,
                    wheelbase=preset['wheelbase'] / 1000.0,
                    front_overhang=preset.get('front_overhang', 0.9) / 1000.0,
                    rear_overhang=preset.get('rear_overhang', 0.8) / 1000.0,
                    hood_angle=preset.get('hood_angle', 12.0),
                    roof_arc=preset.get('roof_arc', 0.3),
                    windshield_angle=preset.get('windshield_angle', 30.0),
                    rear_window_angle=preset.get('rear_window_angle', 25.0),
                    wheel_arch_bulge=preset.get('wheel_arch', 50) / 1000.0,
                    waistline_ratio=preset.get('waistline', 0.75),
                )
            
            # Try to build the part
            # Note: This requires the build_xxx functions to be available
            # For now, we test via build_full_car_geometric
            all_parts = build_full_car_geometric(params)
            
            if part_name not in all_parts:
                self.add_error(part_name, f'Part not found in build_full_car_geometric output')
                return
            
            part_data = all_parts[part_name]
            
            # Validate geometry
            geo_result = self.validate_geometry(part_name, part_data)
            self.results['geometry_tests'].append(geo_result)
            
            if not geo_result['passed']:
                for check_name, passed, msg in geo_result['checks']:
                    if not passed:
                        self.add_error(part_name, msg)
            else:
                stats = geo_result['stats']
                self.add_pass(part_name, 
                    f"verts={stats['vertex_count']}, faces={stats['face_count']}, "
                    f"bbox=[{stats['bbox_size'][0]:.3f}, {stats['bbox_size'][1]:.3f}, {stats['bbox_size'][2]:.3f}]")
            
        except Exception as e:
            self.add_error(part_name, f'Exception: {e}')
    
    def test_all_parts(self):
        """Test all parts from build_full_car_geometric"""
        self.log("\n" + "="*60)
        self.log("🚗 Testing ALL parts from build_full_car_geometric()")
        self.log("="*60)
        
        if not APP_LOADED:
            self.add_error('all_parts', 'app.py not loaded')
            return
        
        try:
            # Create params directly from CAR_TYPE_PRESETS
            preset = CAR_TYPE_PRESETS['sedan']
            params = CoreCarParams(
                length=preset['length'] / 1000.0,
                width=preset['width'] / 1000.0,
                height=preset['height'] / 1000.0,
                wheelbase=preset['wheelbase'] / 1000.0,
                front_overhang=preset.get('front_overhang', 0.9) / 1000.0,
                rear_overhang=preset.get('rear_overhang', 0.8) / 1000.0,
                hood_angle=preset.get('hood_angle', 12.0),
                roof_arc=preset.get('roof_arc', 0.3),
                windshield_angle=preset.get('windshield_angle', 30.0),
                rear_window_angle=preset.get('rear_window_angle', 25.0),
                wheel_arch_bulge=preset.get('wheel_arch', 50) / 1000.0,
                waistline_ratio=preset.get('waistline', 0.75),
            )
            all_parts = build_full_car_geometric(params)
            
            self.log(f"\nTotal parts: {len(all_parts)}")
            
            for part_name in sorted(all_parts.keys()):
                self.test_single_part(part_name, params)
            
        except Exception as e:
            self.add_error('all_parts', f'Exception: {e}')
    
    # ====== Rendering Tests ======
    
    def test_render_single_part(self, part_name: str, output_format: str = 'png'):
        """Test rendering a single part to an image"""
        self.log(f"\n🎨 Rendering part: {part_name}")
        
        if not APP_LOADED:
            self.add_error(part_name, 'app.py not loaded')
            return
        
        try:
            # Create params directly from CAR_TYPE_PRESETS
            preset = CAR_TYPE_PRESETS['sedan']
            params = CoreCarParams(
                length=preset['length'] / 1000.0,
                width=preset['width'] / 1000.0,
                height=preset['height'] / 1000.0,
                wheelbase=preset['wheelbase'] / 1000.0,
                front_overhang=preset.get('front_overhang', 0.9) / 1000.0,
                rear_overhang=preset.get('rear_overhang', 0.8) / 1000.0,
                hood_angle=preset.get('hood_angle', 12.0),
                roof_arc=preset.get('roof_arc', 0.3),
                windshield_angle=preset.get('windshield_angle', 30.0),
                rear_window_angle=preset.get('rear_window_angle', 25.0),
                wheel_arch_bulge=preset.get('wheel_arch', 50) / 1000.0,
                waistline_ratio=preset.get('waistline', 0.75),
            )
            all_parts = build_full_car_geometric(params)
            
            if part_name not in all_parts:
                self.add_error(part_name, 'Part not found')
                return
            
            part_data = all_parts[part_name]
            
            # Try to create a Plotly figure
            import plotly.graph_objects as go
            
            trace = surface_dict_to_plotly(part_data, name=part_name, color='#C0C0C0', opacity=0.9)
            fig = go.Figure(data=[trace])
            fig.update_layout(
                scene=dict(
                    aspectmode='data',
                    xaxis=dict(title='X (m)'),
                    yaxis=dict(title='Y (m)'),
                    zaxis=dict(title='Z (m)'),
                ),
                title=part_name,
            )
            
            # Export
            if output_format == 'png':
                output_path = self.output_dir / f'{part_name}.png'
                fig.write_image(str(output_path), width=800, height=600)
                self.add_pass(part_name, f'Rendered to {output_path.name}')
            elif output_format == 'html':
                output_path = self.output_dir / f'{part_name}.html'
                fig.write_html(str(output_path))
                self.add_pass(part_name, f'Rendered to {output_path.name}')
            
            self.results['render_tests'].append({
                'part': part_name,
                'format': output_format,
                'output': str(output_path),
                'success': True,
            })
            
        except Exception as e:
            self.add_error(part_name, f'Render failed: {e}')
            self.results['render_tests'].append({
                'part': part_name,
                'format': output_format,
                'success': False,
                'error': str(e),
            })
    
    # ====== Export Tests ======
    
    def export_part_obj(self, part_name: str):
        """Export a single part as OBJ file"""
        self.log(f"\n📦 Exporting part: {part_name}")
        
        if not APP_LOADED:
            self.add_error(part_name, 'app.py not loaded')
            return
        
        try:
            # Create params directly from CAR_TYPE_PRESETS
            preset = CAR_TYPE_PRESETS['sedan']
            params = CoreCarParams(
                length=preset['length'] / 1000.0,
                width=preset['width'] / 1000.0,
                height=preset['height'] / 1000.0,
                wheelbase=preset['wheelbase'] / 1000.0,
                front_overhang=preset.get('front_overhang', 0.9) / 1000.0,
                rear_overhang=preset.get('rear_overhang', 0.8) / 1000.0,
                hood_angle=preset.get('hood_angle', 12.0),
                roof_arc=preset.get('roof_arc', 0.3),
                windshield_angle=preset.get('windshield_angle', 30.0),
                rear_window_angle=preset.get('rear_window_angle', 25.0),
                wheel_arch_bulge=preset.get('wheel_arch', 50) / 1000.0,
                waistline_ratio=preset.get('waistline', 0.75),
            )
            all_parts = build_full_car_geometric(params)
            
            if part_name not in all_parts:
                self.add_error(part_name, 'Part not found')
                return
            
            part_data = all_parts[part_name]
            verts = part_data['vertices']
            faces = part_data['faces']
            
            # Write OBJ
            output_path = self.output_dir / f'{part_name}.obj'
            with open(output_path, 'w') as f:
                f.write(f"# Part: {part_name}\n")
                f.write(f"# Vertices: {len(verts)}\n")
                f.write(f"# Faces: {len(faces)}\n")
                
                for v in verts:
                    f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
                
                for face in faces:
                    # OBJ uses 1-based indexing
                    f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1}\n")
            
            self.add_pass(part_name, f'Exported to {output_path.name} ({output_path.stat().st_size} bytes)')
            
            self.results['export_tests'].append({
                'part': part_name,
                'format': 'obj',
                'output': str(output_path),
                'size': output_path.stat().st_size,
                'success': True,
            })
            
        except Exception as e:
            self.add_error(part_name, f'Export failed: {e}')
            self.results['export_tests'].append({
                'part': part_name,
                'format': 'obj',
                'success': False,
                'error': str(e),
            })
    
    # ====== Report ======
    
    def generate_report(self):
        """Generate a summary report"""
        self.log("\n" + "="*60)
        self.log("📊 TEST REPORT")
        self.log("="*60)
        
        total_tests = len(self.results['geometry_tests']) + len(self.results['render_tests']) + len(self.results['export_tests'])
        passed_tests = sum(1 for t in self.results['geometry_tests'] if t['passed'])
        failed_tests = len(self.results['errors'])
        
        self.log(f"\nTotal tests: {total_tests}")
        self.log(f"Passed: {passed_tests}")
        self.log(f"Failed: {failed_tests}")
        self.log(f"Warnings: {len(self.results['warnings'])}")
        
        if self.results['errors']:
            self.log("\n❌ ERRORS:")
            for err in self.results['errors']:
                self.log(f"  - {err['test']}: {err['message']}")
        
        if self.results['warnings']:
            self.log("\n⚠️  WARNINGS:")
            for warn in self.results['warnings']:
                self.log(f"  - {warn['test']}: {warn['message']}")
        
        # Save JSON report
        report_path = self.output_dir / 'test_report.json'
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        self.log(f"\n📄 Full report saved to: {report_path}")
        
        return failed_tests == 0


def main():
    parser = argparse.ArgumentParser(description='3D Rendering Self-Test Validator')
    parser.add_argument('--part', type=str, help='Test a single part by name')
    parser.add_argument('--group', type=str, choices=['wheels', 'glass', 'body', 'all'], help='Test a group of parts')
    parser.add_argument('--export', type=str, choices=['obj'], help='Export parts to file format')
    parser.add_argument('--render', type=str, choices=['png', 'html'], help='Render parts to image format')
    parser.add_argument('--output-dir', type=Path, help='Output directory for exports and renders')
    
    args = parser.parse_args()
    
    validator = RenderValidator(output_dir=args.output_dir)
    
    if args.part:
        # Test single part
        validator.test_single_part(args.part)
        if args.export:
            validator.export_part_obj(args.part)
        if args.render:
            validator.test_render_single_part(args.part, args.render)
    
    elif args.group:
        # Test group of parts
        if not APP_LOADED:
            print("❌ app.py not loaded")
            sys.exit(1)
        
        params = build_params_from_preset('sedan')
        all_parts = build_full_car_geometric(params)
        
        groups = {
            'wheels': ['wheel_fr', 'wheel_fl', 'wheel_rr', 'wheel_rl'],
            'glass': ['windshield', 'rear_window', 'window_front_right', 'window_front_left',
                      'window_rear_right', 'window_rear_left'],
            'body': ['side_right', 'side_left', 'top', 'hood', 'trunk_lid'],
        }
        
        if args.group == 'all':
            validator.test_all_parts()
        else:
            for part_name in groups.get(args.group, []):
                validator.test_single_part(part_name, params)
                if args.export:
                    validator.export_part_obj(part_name)
                if args.render:
                    validator.test_render_single_part(part_name, args.render)
    
    else:
        # Test all parts
        validator.test_all_parts()
    
    # Generate report
    all_passed = validator.generate_report()
    
    sys.exit(0 if all_passed else 1)


if __name__ == '__main__':
    main()
