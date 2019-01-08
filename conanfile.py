from conans import ConanFile, tools, MSBuild
from conanos.build import config_scheme
import os, shutil


class FfmpegConan(ConanFile):
    name = "FFmpeg"
    version = "3.3.4.r87868"
    description = "FFmpeg is a collection of libraries and tools to process multimedia content such as audio, video, subtitles and related metadata."
    url = "https://github.com/conanos/FFmpeg"
    homepage = "https://ffmpeg.org"
    license = "LGPL-v2.1+,GPL-v2+"
    exports = ["COPYING.*", "pc/*"]
    generators = "visual_studio", "gcc"
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = { 'shared': True, 'fPIC': True }

    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        del self.settings.compiler.libcxx

        config_scheme(self)

    def requirements(self):
        self.requires.add("nv-codec-headers/n8.2.15.6@conanos/stable")
        self.requires.add("mfx_dispatch/1.27.r60@conanos/stable")
        self.requires.add("soxr/0.1.3@conanos/stable")
        self.requires.add("libiconv/1.15@conanos/stable")
        self.requires.add("zlib/1.2.11@conanos/stable")
        self.requires.add("lame/3.100@conanos/stable")
        self.requires.add("opus/1.2.1@conanos/stable")
        self.requires.add("speex/1.2.0@conanos/stable")
        self.requires.add("libvorbis/1.3.6@conanos/stable")
        self.requires.add("libvpx/1.7.0@conanos/stable")
        self.requires.add("libtheora/1.1.1@conanos/stable")
        self.requires.add("x264/0.152.r2854@conanos/stable")
        self.requires.add("AMF/1.4.9@conanos/stable")
        self.requires.add("lzma/5.2.4@conanos/stable")
        self.requires.add("xvid/1.3.4-3@conanos/stable")
        self.requires.add("libilbc/2.0.2-2@conanos/stable")
        self.requires.add("x265/2.8@conanos/stable")
        self.requires.add("bzip2/1.0.6@conanos/stable")
        self.requires.add("libxml2/2.9.8@conanos/stable")
        self.requires.add("gnutls/3.5.19@conanos/stable")
        self.requires.add("libgcrypt/1.8.4@conanos/stable")
        self.requires.add("modplug/0.8.9.0.r274@conanos/stable")
        self.requires.add("libbluray/1.0.2-3@conanos/stable")
        self.requires.add("libssh/0.8.6@conanos/stable")
        self.requires.add("game-music-emu/0.6.2@conanos/stable")
        self.requires.add("libass/0.14.0-13@conanos/stable")
        self.requires.add("fribidi/1.0.5@conanos/stable")
        self.requires.add("SDL/2.0.9@conanos/stable")
        self.requires.add("libcdio/2.0.0@conanos/stable")
        self.requires.add("libcdio-paranoia/10.2-0.94-2-3@conanos/stable")
        self.requires.add("OpenGL/master@conanos/stable")


    def source(self):
        url_ = 'https://github.com/ShiftMediaProject/FFmpeg/archive/{version}.tar.gz'
        tools.get(url_.format(version=self.version))
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self._source_subfolder)

    def build(self):
        if self.settings.os == 'Windows':
            with tools.chdir(os.path.join(self._source_subfolder,"SMP")):
                replacements = {
                    "bz2d.lib"        :  "bz2.lib",
                    "iconvd.lib"      :  "iconv.lib",
                    "zlibd.lib"       :  "zlib.lib",
                    "opusd.lib"       :  "opus.lib",
                    "speexd.lib"      :  "libspeex.lib",
                    "theorad.lib"     :  "libtheora.lib",
                    "vorbisd.lib"     :  "vorbis.lib",
                    "xml2d.lib"       :  "libxml2.lib",
                    "fontconfigd.lib" :  "fontconfig.lib",
                    "fribidid.lib"    :  "fribidi.lib",
                }
                for proj in ["libavcodec.vcxproj","libavformat.vcxproj","libavfilter.vcxproj"]:
                    for s, r in replacements.items():
                        tools.replace_in_file(proj, s,r,strict=False)

                include = [ os.path.join(self.deps_cpp_info["fribidi"].rootpath, "include","fribidi"),
                            os.path.join(self.deps_cpp_info["SDL"].rootpath, "include","SDL") ]
                with tools.environment_append({
                    "INCLUDE" : os.pathsep.join(include + [os.getenv('INCLUDE')]),
                    }):
                    msbuild = MSBuild(self)
                    build_type = str(self.settings.build_type) + ("DLL" if self.options.shared else "")
                    msbuild.build("ffmpeg.sln",upgrade_project=True,platforms={'x86': 'Win32', 'x86_64': 'x64'},build_type=build_type)

    def package(self):
        if self.settings.os == 'Windows':
            platforms={'x86': 'Win32', 'x86_64': 'x64'}
            rplatform = platforms.get(str(self.settings.arch))
            self.copy("*", dst=os.path.join(self.package_folder,"include"), src=os.path.join(self.build_folder,"..", "msvc","include"))
            if self.options.shared:
                for i in ["lib","bin"]:
                    self.copy("*", dst=os.path.join(self.package_folder,i), src=os.path.join(self.build_folder,"..","msvc",i,rplatform))
            self.copy("*", dst=os.path.join(self.package_folder,"licenses"), src=os.path.join(self.build_folder,"..", "msvc","licenses"))

            tools.mkdir(os.path.join(self.package_folder,"lib","pkgconfig"))
            for name in ["avcodec","avdevice","avfilter","avformat","avutil","swresample","swscale"]:
                lib = "-l"+name+"d" if self.options.shared else "-l"+name
                shutil.copy(os.path.join(self.build_folder,"pc","lib"+name+".pc.in"),
                            os.path.join(self.package_folder,"lib","pkgconfig","lib"+name+".pc"))
                replacements = {
                    "@prefix@" : self.package_folder,
                    "-l"+name  : lib 
                }
                if name == "avcodec":
                    replacements.update({"@version@":"57.108.100"})
                if name == "avdevice":
                    replacements.update({"@version@":"57.11.100"})
                if name == "avfilter":
                    replacements.update({"@version@":"6.108.100"})
                if name == "avformat":
                    replacements.update({"@version@":"57.84.100"})
                if name == "avutil":
                    replacements.update({"@version@":"55.79.100"})
                if name == "swresample":
                    replacements.update({"@version@":"2.10.100"})
                if name == "swscale":
                    replacements.update({"@version@":"4.9.100"})
                for s, r in replacements.items():
                    tools.replace_in_file(os.path.join(self.package_folder,"lib","pkgconfig","lib"+name+".pc"),s,r)
            
            

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)

